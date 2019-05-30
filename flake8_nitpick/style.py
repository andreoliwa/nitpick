# -*- coding: utf-8 -*-
"""Style files."""
import logging
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Set
from urllib.parse import urlparse, urlunparse

import requests
import toml
from slugify import slugify

from flake8_nitpick.constants import (
    DEFAULT_NITPICK_STYLE_URL,
    LOG_ROOT,
    NITPICK_STYLE_TOML,
    NITPICK_STYLES_INCLUDE_JMEX,
    TOML_EXTENSION,
    UNIQUE_SEPARATOR,
)
from flake8_nitpick.files.pyproject_toml import PyProjectTomlFile
from flake8_nitpick.generic import climb_directory_tree, flatten, is_url, search_dict, unflatten
from flake8_nitpick.typedefs import JsonDict, StrOrList

if TYPE_CHECKING:
    from flake8_nitpick.config import NitpickConfig

LOGGER = logging.getLogger(f"{LOG_ROOT}.style")


class Style:
    """Include styles recursively from one another."""

    def __init__(self, config: "NitpickConfig") -> None:
        self.config = config
        self._all_flattened: JsonDict = {}
        self._already_included: Set[str] = set()
        self._first_full_path: str = ""

    def find_initial_styles(self, configured_styles: StrOrList):
        """Find the initial style(s) and include them."""
        if configured_styles:
            chosen_styles = configured_styles
            log_message = f"Styles configured in {PyProjectTomlFile.file_name}: %s"
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
        style_uris: List[str] = [chosen_styles] if isinstance(chosen_styles, str) else chosen_styles
        for style_uri in style_uris:
            style_path: Optional[Path] = self.get_style_path(style_uri)
            if not style_path:
                continue

            toml_dict = toml.load(str(style_path))
            flattened_style_dict: JsonDict = flatten(toml_dict, separator=UNIQUE_SEPARATOR)
            self._all_flattened.update(flattened_style_dict)

            sub_styles: StrOrList = search_dict(NITPICK_STYLES_INCLUDE_JMEX, toml_dict, [])
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
            resolved = (Path(rest) / url).resolve()
            new_url = f"{prefix}:/{resolved}"
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
            raise FileNotFoundError(f"Error {response} fetching style URL {new_url}")

        # Save the first full path to be used by the next files without parent.
        if not self._first_full_path:
            self._first_full_path = new_url.rsplit("/", 1)[0]

        contents = response.text
        style_path = self.config.cache_dir / f"{slugify(new_url)}.toml"
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
            raise FileNotFoundError(f"Local style file does not exist: {style_path}")

        LOGGER.info("Loading style from file: %s", style_path)
        self._already_included.add(str(style_path))
        return style_path

    def merge_toml_dict(self) -> JsonDict:
        """Merge all included styles into a TOML (actually JSON) dictionary."""
        return unflatten(self._all_flattened, separator=UNIQUE_SEPARATOR)
