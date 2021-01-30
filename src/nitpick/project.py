"""A project to be nitpicked."""
import itertools
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Iterator, Optional, Set, Union

import pluggy
from autorepr import autorepr
from loguru import logger
from marshmallow_polyfield import PolyField
from pluggy import PluginManager

from nitpick import fields, plugins
from nitpick.constants import (
    MANAGE_PY,
    NITPICK_MINIMUM_VERSION_JMEX,
    PROJECT_NAME,
    PYPROJECT_TOML,
    ROOT_FILES,
    ROOT_PYTHON_FILES,
    TOOL_NITPICK,
    TOOL_NITPICK_JMEX,
)
from nitpick.exceptions import MinimumVersionError, NitpickError, NoPythonFileError, NoRootDirError, StyleError
from nitpick.formats import TOMLFormat
from nitpick.generic import search_dict, version_to_tuple
from nitpick.schemas import BaseNitpickSchema, flatten_marshmallow_errors, help_message
from nitpick.typedefs import JsonDict, PathOrStr, StrOrList, mypy_property


def climb_directory_tree(starting_path: PathOrStr, file_patterns: Iterable[str]) -> Optional[Set[Path]]:
    """Climb the directory tree looking for file patterns."""
    current_dir = Path(starting_path).absolute()  # type: Path
    if current_dir.is_file():
        current_dir = current_dir.parent

    while current_dir.anchor != str(current_dir):
        for root_file in file_patterns:
            found_files = list(current_dir.glob(root_file))
            if found_files:
                return set(found_files)
        current_dir = current_dir.parent
    return None


# TODO: add unit tests with tmp_path https://docs.pytest.org/en/stable/tmpdir.html
def find_root() -> Path:
    """Find the root dir of the Python project (the one that has one of the ``ROOT_FILES``).

    Start from the current working dir.
    """
    # FIXME[AA]: add logging here
    root_dirs: Set[Path] = set()
    seen: Set[Path] = set()

    all_files = list(Path.cwd().glob("*"))
    # Don't fail if the current dir is empty
    starting_file = str(all_files[0]) if all_files else ""
    starting_dir = Path(starting_file).parent.absolute()
    while True:
        project_files = climb_directory_tree(starting_dir, ROOT_FILES)
        if project_files and project_files & seen:
            break
        seen.update(project_files or [])

        if not project_files:
            # If none of the root files were found, try again with manage.py.
            # On Django projects, it can be in another dir inside the root dir.
            project_files = climb_directory_tree(starting_file, [MANAGE_PY])
            if not project_files or project_files & seen:
                break
            seen.update(project_files)

        for found in project_files or []:
            root_dirs.add(found.parent)

        # Climb up one directory to search for more project files
        starting_dir = starting_dir.parent
        if not starting_dir:
            break

    if not root_dirs:
        logger.error("No files found while climbing directory tree from {}", str(starting_file))
        raise NoRootDirError()

    # If multiple roots are found, get the top one (grandparent dir)
    return sorted(root_dirs)[0]


class ToolNitpickSectionSchema(BaseNitpickSchema):
    """Validation schema for the ``[tool.nitpick]`` section on ``pyproject.toml``."""

    error_messages = {"unknown": help_message("Unknown configuration", "tool_nitpick_section.html")}

    style = PolyField(deserialization_schema_selector=fields.string_or_list_field)


class Project:
    """A project to be nitpicked."""

    __repr__ = autorepr(["_supplied_root", "root"])

    def __init__(self, root: Union[Path, str] = None) -> None:
        self._supplied_root = root

        self.pyproject_toml: Optional[TOMLFormat] = None
        self.tool_nitpick_dict: JsonDict = {}
        self.style_dict: JsonDict = {}
        self.nitpick_section: JsonDict = {}
        self.nitpick_files_section: JsonDict = {}

    @mypy_property
    @lru_cache()
    def root(self) -> Path:
        """Root dir of the project."""
        if self._supplied_root:
            return Path(self._supplied_root)
        return find_root()

    def find_main_python_file(self) -> Path:  # TODO: add unit tests
        """Find the main Python file in the root dir, the one that will be used to report Flake8 warnings.

        The search order is:
        1. Python files that belong to the root dir of the project (e.g.: ``setup.py``, ``autoapp.py``).
        2. ``manage.py``: they can be on the root or on a subdir (Django projects).
        3. Any other ``*.py`` Python file on the root dir and subdir.
        This avoid long recursions when there is a ``node_modules`` subdir for instance.
        """
        for the_file in itertools.chain(
            # 1.
            [self.root / root_file for root_file in ROOT_PYTHON_FILES],
            # 2.
            self.root.glob("*/{}".format(MANAGE_PY)),
            # 3.
            self.root.glob("*.py"),
            self.root.glob("*/*.py"),
        ):
            if the_file.exists():
                logger.info("Found the file {}", the_file)
                return Path(the_file)

        raise NoPythonFileError(self.root)

    @mypy_property
    @lru_cache()
    def plugin_manager(self) -> PluginManager:
        """Load all defined plugins."""
        plugin_manager = pluggy.PluginManager(PROJECT_NAME)
        plugin_manager.add_hookspecs(plugins)
        plugin_manager.load_setuptools_entrypoints(PROJECT_NAME)
        return plugin_manager

    def validate_pyproject_tool_nitpick(self) -> None:
        """Validate the ``pyroject.toml``'s ``[tool.nitpick]`` section against a Marshmallow schema."""
        # pylint: disable=import-outside-toplevel
        pyproject_path: Path = self.root / PYPROJECT_TOML
        if not pyproject_path.exists():
            return

        self.pyproject_toml = TOMLFormat(path=pyproject_path)
        self.tool_nitpick_dict = search_dict(TOOL_NITPICK_JMEX, self.pyproject_toml.as_data, {})
        pyproject_errors = ToolNitpickSectionSchema().validate(self.tool_nitpick_dict)
        if not pyproject_errors:
            return

        raise StyleError(
            PYPROJECT_TOML, f"Invalid data in [{TOOL_NITPICK}]:", flatten_marshmallow_errors(pyproject_errors)
        )

    def merge_styles(self, offline: bool) -> Iterator[NitpickError]:
        """Merge one or multiple style files."""
        try:
            self.validate_pyproject_tool_nitpick()
        except StyleError as err:
            # If the project is misconfigured, don't even continue.
            yield err
            return

        from nitpick.style import Style  # pylint: disable=import-outside-toplevel

        configured_styles: StrOrList = self.tool_nitpick_dict.get("style", "")
        style = Style(self, self.plugin_manager, offline)
        yield from style.find_initial_styles(configured_styles)

        self.style_dict = style.merge_toml_dict()

        from nitpick.flake8 import NitpickExtension  # pylint: disable=import-outside-toplevel

        minimum_version = search_dict(NITPICK_MINIMUM_VERSION_JMEX, self.style_dict, None)
        logger.info(f"Minimum version: {minimum_version}")
        if minimum_version and version_to_tuple(NitpickExtension.version) < version_to_tuple(minimum_version):
            yield MinimumVersionError(minimum_version, NitpickExtension.version)

        self.nitpick_section = self.style_dict.get("nitpick", {})
        self.nitpick_files_section = self.nitpick_section.get("files", {})