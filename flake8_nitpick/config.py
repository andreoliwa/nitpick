"""Configuration of the plugin itself."""
import itertools
import logging
from pathlib import Path
from shutil import rmtree
from typing import Any, Dict, List, MutableMapping, Optional, Set

import requests
import toml
from slugify import slugify

from flake8_nitpick.constants import (
    DEFAULT_NITPICK_STYLE_URL,
    NITPICK_MINIMUM_VERSION_JMEX,
    NITPICK_STYLE_TOML,
    NITPICK_STYLES_INCLUDE_JMEX,
    PROJECT_NAME,
    ROOT_FILES,
    ROOT_PYTHON_FILES,
    TOOL_NITPICK_JMEX,
    UNIQUE_SEPARATOR,
)
from flake8_nitpick.files.pyproject_toml import PyProjectTomlFile
from flake8_nitpick.files.setup_cfg import SetupCfgFile
from flake8_nitpick.generic import (
    climb_directory_tree,
    flatten,
    rmdir_if_empty,
    search_dict,
    unflatten,
    version_to_tuple,
)
from flake8_nitpick.types import JsonDict, PathOrStr, StrOrList, YieldFlake8Error
from flake8_nitpick.utils import NitpickMixin

LOG = logging.getLogger("flake8.nitpick")


class NitpickConfig(NitpickMixin):
    """Plugin configuration, read from the project config."""

    error_base_number = 200

    _singleton_instance: Optional["NitpickConfig"] = None

    def __init__(self) -> None:
        """Init instance."""
        self.root_dir: Optional[Path] = None
        self.cache_dir: Optional[Path] = None
        self.main_python_file: Optional[Path] = None

        self.pyproject_dict: MutableMapping[str, Any] = {}
        self.tool_nitpick_dict: Dict[str, Any] = {}
        self.style_dict: MutableMapping[str, Any] = {}
        self.nitpick_dict: MutableMapping[str, Any] = {}
        self.files: Dict[str, Any] = {}

    @classmethod
    def get_singleton(cls) -> "NitpickConfig":
        """Init the global singleton instance of the plugin configuration, needed by all file checkers."""
        if cls._singleton_instance is None:
            cls._singleton_instance = cls()
        return cls._singleton_instance

    @classmethod
    def reset_singleton(cls):
        """Reset the singleton instance. Useful on automated tests, to simulate ``flake8`` execution."""
        cls._singleton_instance = None

    def find_root_dir(self, starting_file: PathOrStr) -> bool:
        """Find the root dir of the Python project: the dir that has one of the `ROOT_FILES`.

        Also clear the cache dir the first time the root dir is found.
        """
        if self.root_dir:
            return True

        found_files = climb_directory_tree(
            starting_file, ROOT_FILES + (PyProjectTomlFile.file_name, SetupCfgFile.file_name)
        )
        if not found_files:
            LOG.error("No files found while climbing directory tree from %s", str(starting_file))
            return False

        self.root_dir = found_files[0].parent
        self.clear_cache_dir()
        return True

    def find_main_python_file(self) -> bool:
        """Find the main Python file in the root dir, the one that will be used to report Flake8 warnings."""
        if not self.root_dir:
            return False
        for the_file in itertools.chain(
            [self.root_dir / root_file for root_file in ROOT_PYTHON_FILES], self.root_dir.glob("*.py")
        ):
            if the_file.exists():
                self.main_python_file = Path(the_file)
                LOG.info("Found the file %s", the_file)
                return True
        return False

    def clear_cache_dir(self) -> None:
        """Clear the cache directory (on the project root or on the current directory)."""
        if not self.root_dir:
            return
        cache_root: Path = self.root_dir / ".cache"
        self.cache_dir = cache_root / PROJECT_NAME
        rmtree(str(self.cache_dir), ignore_errors=True)
        rmdir_if_empty(cache_root)

    def load_toml(self) -> YieldFlake8Error:  # FIXME: fetch_initial_style
        """Fetch the initial style for one or multiple style files."""
        pyproject_path: Path = self.root_dir / PyProjectTomlFile.file_name
        if pyproject_path.exists():
            self.pyproject_dict: JsonDict = toml.load(str(pyproject_path))
            self.tool_nitpick_dict: JsonDict = search_dict(TOOL_NITPICK_JMEX, self.pyproject_dict, {})

        configured_styles: StrOrList = self.tool_nitpick_dict.get("style", "")
        if configured_styles:
            chosen_styles = configured_styles
        else:
            paths = climb_directory_tree(self.root_dir, [NITPICK_STYLE_TOML])
            if paths:
                chosen_styles = str(paths[0])
                LOG.info("Found style climbing the directory tree: %s", chosen_styles)
            else:
                chosen_styles = DEFAULT_NITPICK_STYLE_URL
                LOG.info("Loading default Nitpick style %s", DEFAULT_NITPICK_STYLE_URL)

        tree = StyleTree(self.cache_dir)
        tree.include_styles(chosen_styles)
        self.style_dict = tree.merge_toml_dict()

        minimum_version = search_dict(NITPICK_MINIMUM_VERSION_JMEX, self.style_dict, None)
        from flake8_nitpick.plugin import NitpickChecker

        if minimum_version and version_to_tuple(NitpickChecker.version) < version_to_tuple(minimum_version):
            yield self.flake8_error(
                3,
                f"The style file you're using requires {PROJECT_NAME}>={minimum_version}"
                + f" (you have {NitpickChecker.version}). Please upgrade",
            )

        self.nitpick_dict: JsonDict = self.style_dict.get("nitpick", {})
        self.files = self.nitpick_dict.get("files", {})


class StyleTree:
    """Class to include styles recursively from one another."""

    def __init__(self, cache_dir: Optional[Path]) -> None:
        self.cache_dir: Optional[Path] = cache_dir
        self._all_flattened: JsonDict = {}
        self._already_included: Set[str] = set()

    def include_styles(self, chosen_styles: StrOrList) -> None:
        """Include one style or a list of styles into this style tree."""
        style_uris: List[str] = [chosen_styles] if isinstance(chosen_styles, str) else chosen_styles

        for style_uri in style_uris:
            clean_style_uri = style_uri.strip()
            if clean_style_uri.startswith("http"):
                if clean_style_uri in self._already_included:
                    continue

                # If the style is a URL, save the contents in the cache dir
                style_path = self.load_style_from_url(clean_style_uri)
                LOG.info("Loading style from URL %s into %s", clean_style_uri, style_path)
                self._already_included.add(clean_style_uri)
            elif clean_style_uri:
                style_path = Path(clean_style_uri).absolute()
                if str(style_path) in self._already_included:
                    continue
                if not style_path.exists():
                    raise FileNotFoundError(f"Style file does not exist: {clean_style_uri}")
                LOG.info("Loading style from file: %s", style_path)
                self._already_included.add(str(style_path))
            else:
                # If the style is an empty string, skip it
                continue
            toml_dict = toml.load(str(style_path))

            sub_styles: StrOrList = search_dict(NITPICK_STYLES_INCLUDE_JMEX, toml_dict, [])

            flattened_style_dict: JsonDict = flatten(toml_dict, separator=UNIQUE_SEPARATOR)
            self._all_flattened.update(flattened_style_dict)

            self.include_styles(sub_styles)

    def load_style_from_url(self, url: str) -> Path:
        """Load a style file from a URL."""
        if not self.cache_dir:
            raise FileNotFoundError("Cache dir does not exist")

        response = requests.get(url)
        if not response.ok:
            raise FileNotFoundError(f"Error {response} fetching style URL {url}")

        contents = response.text
        style_path = self.cache_dir / f"{slugify(url)}.toml"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        style_path.write_text(contents)
        return style_path

    def merge_toml_dict(self) -> JsonDict:
        """Merge all included styles into a TOML (actually JSON) dictionary."""
        return unflatten(self._all_flattened, separator=UNIQUE_SEPARATOR)
