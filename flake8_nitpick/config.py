# -*- coding: utf-8 -*-
"""Configuration of the plugin."""
import itertools
import logging
from pathlib import Path
from shutil import rmtree
from typing import Any, Dict, MutableMapping, Optional

import toml

from flake8_nitpick.constants import (
    LOG_ROOT,
    MANAGE_PY,
    NITPICK_MINIMUM_VERSION_JMEX,
    PROJECT_NAME,
    ROOT_FILES,
    ROOT_PYTHON_FILES,
    TOOL_NITPICK_JMEX,
)
from flake8_nitpick.files.pyproject_toml import PyProjectTomlFile
from flake8_nitpick.files.setup_cfg import SetupCfgFile
from flake8_nitpick.generic import climb_directory_tree, rmdir_if_empty, search_dict, version_to_tuple
from flake8_nitpick.mixin import NitpickMixin
from flake8_nitpick.style import Style
from flake8_nitpick.typedefs import JsonDict, PathOrStr, StrOrList, YieldFlake8Error

LOGGER = logging.getLogger(f"{LOG_ROOT}.config")


class NitpickConfig(NitpickMixin):
    """Plugin configuration, read from the project config."""

    error_base_number = 200

    _singleton_instance: Optional["NitpickConfig"] = None
    root_dir: Path
    main_python_file: Path

    def __init__(self) -> None:
        """Init instance."""
        self.cache_dir: Optional[Path] = None

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
        if hasattr(self, "root_dir"):
            return True

        found_files = climb_directory_tree(
            starting_file, ROOT_FILES + (PyProjectTomlFile.file_name, SetupCfgFile.file_name)
        )
        if not found_files:
            # If none of the root files were found, try again with manage.py.
            # On Django projects, it can be in another dir inside the root dir.
            found_files = climb_directory_tree(starting_file, [MANAGE_PY])
            if not found_files:
                LOGGER.error("No files found while climbing directory tree from %s", str(starting_file))
                return False

        self.root_dir = found_files[0].parent
        self.clear_cache_dir()
        return True

    def find_main_python_file(self) -> bool:
        """Find the main Python file in the root dir, the one that will be used to report Flake8 warnings.

        The search order is:
        1. Python files that belong to the root dir of the project (e.g.: ``setup.py``, ``autoapp.py``).
        2. ``manage.py``: they can be on the root or on a subdir (Django projects).
        3. Any other ``*.py`` Python file.
        """
        if not self.root_dir:
            return False
        for the_file in itertools.chain(
            [self.root_dir / root_file for root_file in ROOT_PYTHON_FILES],
            self.root_dir.glob(f"*/{MANAGE_PY}"),
            self.root_dir.glob("*/*.py"),
        ):
            if the_file.exists():
                self.main_python_file = Path(the_file)
                LOGGER.info("Found the file %s", the_file)
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

    def merge_styles(self) -> YieldFlake8Error:
        """Merge one or multiple style files."""
        pyproject_path: Path = self.root_dir / PyProjectTomlFile.file_name
        if pyproject_path.exists():
            self.pyproject_dict: JsonDict = toml.load(str(pyproject_path))
            self.tool_nitpick_dict: JsonDict = search_dict(TOOL_NITPICK_JMEX, self.pyproject_dict, {})

        configured_styles: StrOrList = self.tool_nitpick_dict.get("style", "")
        style = Style(self)
        style.find_initial_styles(configured_styles)
        self.style_dict = style.merge_toml_dict()

        from flake8_nitpick.plugin import NitpickChecker

        minimum_version = search_dict(NITPICK_MINIMUM_VERSION_JMEX, self.style_dict, None)
        if minimum_version and version_to_tuple(NitpickChecker.version) < version_to_tuple(minimum_version):
            yield self.flake8_error(
                3,
                f"The style file you're using requires {PROJECT_NAME}>={minimum_version}"
                + f" (you have {NitpickChecker.version}). Please upgrade",
            )

        self.nitpick_dict: JsonDict = self.style_dict.get("nitpick", {})
        self.files = self.nitpick_dict.get("files", {})
