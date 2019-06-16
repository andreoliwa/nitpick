"""Style files."""
import logging
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Set
from urllib.parse import urlparse, urlunparse

import requests
from slugify import slugify

from nitpick.constants import (
    DEFAULT_NITPICK_STYLE_URL,
    MERGED_STYLE_TOML,
    NITPICK_STYLE_TOML,
    NITPICK_STYLES_INCLUDE_JMEX,
    TOML_EXTENSION,
)
from nitpick.files.pyproject_toml import PyProjectTomlFile
from nitpick.formats import Toml
from nitpick.generic import MergeDict, climb_directory_tree, is_url, search_dict
from nitpick.typedefs import JsonDict, StrOrList

if TYPE_CHECKING:
    from nitpick.config import NitpickConfig

LOGGER = logging.getLogger(__name__)


class Style:
    """Include styles recursively from one another."""

    def __init__(self, config: "NitpickConfig") -> None:
        self.config = config
        self._all_styles = MergeDict()
        self._already_included = set()  # type: Set[str]
        self._first_full_path = ""  # type: str

    def find_initial_styles(self, configured_styles: StrOrList):
        """Find the initial style(s) and include them."""
        if configured_styles:
            chosen_styles = configured_styles
            log_message = "Styles configured in {}: %s".format(PyProjectTomlFile.file_name)
        else:
            paths = climb_directory_tree(self.config.root_dir, [NITPICK_STYLE_TOML])
            if paths:
                chosen_styles = str(paths[0])
                log_message = "Found style climbing the directory tree: %s"
            else:
                chosen_styles = DEFAULT_NITPICK_STYLE_URL
                log_message = "Loading default Nitpick style %s"
        LOGGER.info(log_message, chosen_styles)

        self.include_multiple_styles(chosen_styles)

    def include_multiple_styles(self, chosen_styles: StrOrList) -> None:
        """Include a list of styles (or just one) into this style tree."""
        style_uris = [chosen_styles] if isinstance(chosen_styles, str) else chosen_styles  # type: List[str]
        for style_uri in style_uris:
            style_path = self.get_style_path(style_uri)  # type: Optional[Path]
            if not style_path:
                continue

            toml = Toml(path=style_path)
            self._all_styles.add(toml.as_data)

            sub_styles = search_dict(NITPICK_STYLES_INCLUDE_JMEX, toml.as_data, [])  # type: StrOrList
            if sub_styles:
                self.include_multiple_styles(sub_styles)

    def get_style_path(self, style_uri: str) -> Optional[Path]:
        """Get the style path from the URI. Add the .toml extension if it's missing."""
        clean_style_uri = style_uri.strip()

        style_path = None
        if is_url(clean_style_uri) or is_url(self._first_full_path):
            style_path = self.fetch_style_from_url(clean_style_uri)
        elif clean_style_uri:
            style_path = self.fetch_style_from_local_path(clean_style_uri)
        return style_path

    def fetch_style_from_url(self, url: str) -> Optional[Path]:
        """Fetch a style file from a URL, saving the contents in the cache dir."""
        if self._first_full_path and not is_url(url):
            prefix, rest = self._first_full_path.split(":/")
            domain_plus_url = Path(rest) / url
            try:
                resolved = domain_plus_url.resolve()
            except FileNotFoundError:
                resolved = domain_plus_url.absolute()
            new_url = "{}:/{}".format(prefix, resolved)
        else:
            new_url = url

        parsed_url = list(urlparse(new_url))
        if not parsed_url[2].endswith(TOML_EXTENSION):
            parsed_url[2] += TOML_EXTENSION
        new_url = urlunparse(parsed_url)

        if new_url in self._already_included:
            return None

        if not self.config.cache_dir:
            raise FileNotFoundError("Cache dir does not exist")

        response = requests.get(new_url)
        if not response.ok:
            raise FileNotFoundError("Error {} fetching style URL {}".format(response, new_url))

        # Save the first full path to be used by the next files without parent.
        if not self._first_full_path:
            self._first_full_path = new_url.rsplit("/", 1)[0]

        contents = response.text
        style_path = self.config.cache_dir / "{}.toml".format(slugify(new_url))
        self.config.cache_dir.mkdir(parents=True, exist_ok=True)
        style_path.write_text(contents)

        LOGGER.info("Loading style from URL %s into %s", new_url, style_path)
        self._already_included.add(new_url)

        return style_path

    def fetch_style_from_local_path(self, partial_file_name: str) -> Optional[Path]:
        """Fetch a style file from a local path."""
        if partial_file_name and not partial_file_name.endswith(TOML_EXTENSION):
            partial_file_name += TOML_EXTENSION
        expanded_path = Path(partial_file_name).expanduser()

        if not str(expanded_path).startswith("/") and self._first_full_path:
            # Prepend the previous path to the partial file name.
            style_path = Path(self._first_full_path) / expanded_path
        else:
            # Get the absolute path, be it from a root path (starting with slash) or from the current dir.
            style_path = Path(expanded_path).absolute()

        # Save the first full path to be used by the next files without parent.
        if not self._first_full_path:
            self._first_full_path = str(style_path.resolve().parent)

        if str(style_path) in self._already_included:
            return None

        if not style_path.exists():
            raise FileNotFoundError("Local style file does not exist: {}".format(style_path))

        LOGGER.info("Loading style from file: %s", style_path)
        self._already_included.add(str(style_path))
        return style_path

    def merge_toml_dict(self) -> JsonDict:
        """Merge all included styles into a TOML (actually JSON) dictionary."""
        if not self.config.cache_dir:
            return {}
        merged_dict = self._all_styles.merge()
        merged_style_path = self.config.cache_dir / MERGED_STYLE_TOML  # type: Path
        self.config.cache_dir.mkdir(parents=True, exist_ok=True)
        toml = Toml(data=merged_dict)
        merged_style_path.write_text(toml.reformatted)
        return merged_dict
