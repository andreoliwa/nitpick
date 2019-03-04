"""Configuration of the plugin itself."""
import itertools
import logging
from pathlib import Path
from shutil import rmtree
from typing import Any, Dict, List, MutableMapping, Optional, Union

import requests
import toml
from slugify import slugify

from flake8_nitpick.constants import (
    DEFAULT_NITPICK_STYLE_URL,
    NAME,
    NITPICK_STYLE_TOML,
    ROOT_FILES,
    ROOT_PYTHON_FILES,
    UNIQUE_SEPARATOR,
)
from flake8_nitpick.files.pyproject_toml import PyProjectTomlFile
from flake8_nitpick.files.setup_cfg import SetupCfgFile
from flake8_nitpick.generic import climb_directory_tree, flatten, rmdir_if_empty, unflatten
from flake8_nitpick.types import PathOrStr, TomlDict, YieldFlake8Error
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
        self.cache_dir = cache_root / NAME
        rmtree(str(self.cache_dir), ignore_errors=True)
        rmdir_if_empty(cache_root)

    def load_toml(self) -> YieldFlake8Error:
        """Load TOML configuration from files."""
        pyproject_path: Path = self.root_dir / PyProjectTomlFile.file_name
        if pyproject_path.exists():
            self.pyproject_dict: TomlDict = toml.load(str(pyproject_path))
            self.tool_nitpick_dict: TomlDict = self.pyproject_dict.get("tool", {}).get("nitpick", {})

        try:
            self.style_dict: TomlDict = self.find_styles()
        except FileNotFoundError as err:
            yield self.flake8_error(2, str(err))
            return
        self.nitpick_dict: TomlDict = self.style_dict.get("nitpick", {})
        self.files = self.nitpick_dict.get("files", {})

    def find_styles(self) -> TomlDict:
        """Search for one or multiple style files."""
        style_value: Union[str, List[str]] = self.tool_nitpick_dict.get("style", "")
        styles: List[str] = [style_value] if isinstance(style_value, str) else style_value

        all_flattened: TomlDict = {}
        for style in styles:
            if style.startswith("http"):
                # If the style is a URL, save the contents in the cache dir
                style_path = self.load_style_from_url(style)
                LOG.info("Loading style from URL: %s", style_path)
            elif style:
                style_path = Path(style)
                if not style_path.exists():
                    raise FileNotFoundError(f"Style file does not exist: {style}")
                LOG.info("Loading style from file: %s", style_path)
            else:
                paths = climb_directory_tree(self.root_dir, [NITPICK_STYLE_TOML])
                if paths:
                    style_path = paths[0]
                    LOG.info("Loading style from directory tree: %s", style_path)
                else:
                    style_path = self.load_style_from_url(DEFAULT_NITPICK_STYLE_URL)
                    LOG.info(
                        "Loading default Nitpick style %s into local file %s", DEFAULT_NITPICK_STYLE_URL, style_path
                    )
            flattened_style_dict: TomlDict = flatten(toml.load(str(style_path)), separator=UNIQUE_SEPARATOR)
            all_flattened.update(flattened_style_dict)
        return unflatten(all_flattened, separator=UNIQUE_SEPARATOR)

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
