"""A project to be nitpicked."""
import itertools
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Set, Union

import pluggy
from autorepr import autorepr
from loguru import logger
from marshmallow_polyfield import PolyField
from more_itertools import peekable
from more_itertools.more import always_iterable
from pluggy import PluginManager
from tomlkit import comment, document, dumps, table
from tomlkit.items import Key, KeyType

from nitpick import fields, plugins
from nitpick.constants import (
    CONFIG_FILES,
    DOT_NITPICK_TOML,
    MANAGE_PY,
    NITPICK_MINIMUM_VERSION_JMEX,
    PROJECT_NAME,
    PYPROJECT_TOML,
    READ_THE_DOCS_URL,
    ROOT_FILES,
    ROOT_PYTHON_FILES,
    TOOL_NITPICK,
    TOOL_NITPICK_JMEX,
)
from nitpick.exceptions import QuitComplainingError
from nitpick.formats import TOMLFormat
from nitpick.generic import search_dict, version_to_tuple
from nitpick.schemas import BaseNitpickSchema, flatten_marshmallow_errors, help_message
from nitpick.typedefs import JsonDict, PathOrStr, mypy_property
from nitpick.violations import Fuss, ProjectViolations, Reporter, StyleViolations


def climb_directory_tree(starting_path: PathOrStr, file_patterns: Iterable[str]) -> Set[Path]:  # TODO: add unit test
    """Climb the directory tree looking for file patterns."""
    current_dir: Path = Path(starting_path).absolute()
    while current_dir.anchor != str(current_dir):
        for root_file in file_patterns:
            found_files = list(current_dir.glob(root_file))
            if found_files:
                return set(found_files)
        current_dir = current_dir.parent
    return set()


def find_starting_dir(current_dir: PathOrStr) -> Path:
    """Find the starting dir from the current dir."""
    logger.debug(f"Searching root from current dir: {str(current_dir)!r}")
    all_files_dirs = list(Path(current_dir).glob("*"))
    logger.debug("All files/dirs in the current dir:\n{}", "\n".join(str(file) for file in all_files_dirs))

    # Don't fail if the current dir is empty
    starting_file = str(all_files_dirs[0]) if all_files_dirs else ""
    if starting_file:
        return Path(starting_file).parent.absolute()

    return Path(current_dir).absolute()


def find_root(current_dir: Optional[PathOrStr] = None) -> Path:
    """Find the root dir of the Python project (the one that has one of the ``ROOT_FILES``).

    Start from the current working dir.
    """
    root_dirs: Set[Path] = set()
    seen: Set[Path] = set()

    starting_dir = find_starting_dir(current_dir or Path.cwd())
    while starting_dir:  # pragma: no cover # starting_dir will always have a value on the first run
        logger.debug(f"Climbing dir: {starting_dir}")
        project_files = climb_directory_tree(starting_dir, ROOT_FILES)
        if project_files and project_files & seen:
            break
        seen.update(project_files)
        logger.debug(f"Project files seen: {str(project_files)}")

        if not project_files:
            # If none of the root files were found, try again with manage.py.
            # On Django projects, it can be in another dir inside the root dir.
            project_files = climb_directory_tree(starting_dir, [MANAGE_PY])
            if not project_files or project_files & seen:
                break
            seen.update(project_files)
            logger.debug(f"Django project files seen: {project_files}")

        for found in project_files:
            root_dirs.add(found.parent)
        logger.debug(f"Root dirs: {str(root_dirs)}")

        # Climb up one directory to search for more project files
        starting_dir = starting_dir.parent

    if not root_dirs:
        logger.error(f"No files found while climbing directory tree from {starting_dir}")
        raise QuitComplainingError(Reporter().make_fuss(ProjectViolations.NO_ROOT_DIR))

    # If multiple roots are found, get the top one (grandparent dir)
    top_dir = sorted(root_dirs)[0]
    logger.debug(f"Top root dir found: {top_dir}")
    return top_dir


def find_main_python_file(root_dir: Path) -> Path:
    """Find the main Python file in the root dir, the one that will be used to report Flake8 warnings.

    The search order is:
    1. Python files that belong to the root dir of the project (e.g.: ``setup.py``, ``autoapp.py``).
    2. ``manage.py``: they can be on the root or on a subdir (Django projects).
    3. Any other ``*.py`` Python file on the root dir and subdir.
    This avoid long recursions when there is a ``node_modules`` subdir for instance.
    """
    for the_file in itertools.chain(
        # 1.
        [root_dir / root_file for root_file in ROOT_PYTHON_FILES],
        # 2.
        root_dir.glob(f"*/{MANAGE_PY}"),
        # 3.
        root_dir.glob("*.py"),
        root_dir.glob("*/*.py"),
    ):
        if the_file.exists():
            logger.info(f"Found the file {the_file}")
            return Path(the_file)

    raise QuitComplainingError(Reporter().make_fuss(ProjectViolations.NO_PYTHON_FILE, root=str(root_dir)))


class ToolNitpickSectionSchema(BaseNitpickSchema):
    """Validation schema for the ``[tool.nitpick]`` section on ``pyproject.toml``."""

    error_messages = {"unknown": help_message("Unknown configuration", "configuration.html")}

    style = PolyField(deserialization_schema_selector=fields.string_or_list_field)
    cache = fields.NonEmptyString()


@dataclass
class Configuration:
    """Configuration read from one of the ``CONFIG_FILES``."""

    file: Optional[Path]
    styles: Union[str, List[str]]
    cache: str


class Project:
    """A project to be nitpicked."""

    __repr__ = autorepr(["_chosen_root", "root"])

    def __init__(self, root: PathOrStr = None) -> None:
        self._chosen_root = root

        self.style_dict: JsonDict = {}
        self.nitpick_section: JsonDict = {}
        self.nitpick_files_section: JsonDict = {}

    @mypy_property
    @lru_cache()
    def root(self) -> Path:
        """Root dir of the project."""
        return find_root(self._chosen_root)

    @mypy_property
    @lru_cache()
    def plugin_manager(self) -> PluginManager:
        """Load all defined plugins."""
        plugin_manager = pluggy.PluginManager(PROJECT_NAME)
        plugin_manager.add_hookspecs(plugins)
        plugin_manager.load_setuptools_entrypoints(PROJECT_NAME)
        return plugin_manager

    def read_configuration(self) -> Configuration:
        """Search for a configuration file and validate it against a Marshmallow schema."""
        config_file: Optional[Path] = None
        for possible_file in CONFIG_FILES:
            path: Path = self.root / possible_file
            if not path.exists():
                continue

            if not config_file:
                logger.info(f"Config file: reading from {path}")
                config_file = path
            else:
                logger.warning(f"Config file: ignoring existing {path}")

        if not config_file:
            logger.warning("Config file: none found")
            return Configuration(None, [], "")

        toml_format = TOMLFormat(path=config_file)
        config_dict = search_dict(TOOL_NITPICK_JMEX, toml_format.as_data, {})
        validation_errors = ToolNitpickSectionSchema().validate(config_dict)
        if not validation_errors:
            return Configuration(config_file, config_dict.get("style", []), config_dict.get("cache", ""))

        # pylint: disable=import-outside-toplevel
        from nitpick.plugins.info import FileInfo

        raise QuitComplainingError(
            Reporter(FileInfo(self, PYPROJECT_TOML)).make_fuss(
                StyleViolations.INVALID_DATA_TOOL_NITPICK,
                flatten_marshmallow_errors(validation_errors),
                section=TOOL_NITPICK,
            )
        )

    def merge_styles(self, offline: bool) -> Iterator[Fuss]:
        """Merge one or multiple style files."""
        config = self.read_configuration()

        # pylint: disable=import-outside-toplevel
        from nitpick.style import Style

        style = Style(self, offline, config.cache)
        style_errors = list(style.find_initial_styles(peekable(always_iterable(config.styles))))
        if style_errors:
            raise QuitComplainingError(style_errors)

        self.style_dict = style.merge_toml_dict()

        from nitpick.flake8 import NitpickFlake8Extension

        minimum_version = search_dict(NITPICK_MINIMUM_VERSION_JMEX, self.style_dict, None)
        logger.debug(f"Minimum version: {minimum_version}")
        if minimum_version and version_to_tuple(NitpickFlake8Extension.version) < version_to_tuple(minimum_version):
            yield Reporter().make_fuss(
                ProjectViolations.MINIMUM_VERSION,
                project=PROJECT_NAME,
                expected=minimum_version,
                actual=NitpickFlake8Extension.version,
            )

        self.nitpick_section = self.style_dict.get("nitpick", {})
        self.nitpick_files_section = self.nitpick_section.get("files", {})

    def create_configuration(self) -> None:
        """Create a configuration file."""
        from nitpick.style import Style  # pylint: disable=import-outside-toplevel

        doc = document()
        doc.add(comment("This file was generated by the `nitpick init` command"))
        doc.add(comment(f"More info at {READ_THE_DOCS_URL}configuration.html"))
        doc.add(Key(TOOL_NITPICK, KeyType.Bare), table().add("style", [Style.get_default_style_url()]))

        path: Path = self.root / DOT_NITPICK_TOML
        path.write_text(dumps(doc, sort_keys=True))
