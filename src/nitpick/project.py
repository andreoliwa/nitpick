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
from tomlkit import comment, document, dumps, parse, table
from tomlkit.items import KeyType, SingleKey
from tomlkit.toml_document import TOMLDocument

from nitpick import fields, plugins
from nitpick.blender import TomlDoc, search_json
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
    TOOL_NITPICK_JMEX,
    TOOL_NITPICK_KEY,
)
from nitpick.exceptions import QuitComplainingError
from nitpick.generic import version_to_tuple
from nitpick.schemas import BaseNitpickSchema, flatten_marshmallow_errors, help_message
from nitpick.typedefs import JsonDict, PathOrStr, mypy_property
from nitpick.violations import Fuss, ProjectViolations, Reporter, StyleViolations


def glob_files(dir_: Path, file_patterns: Iterable[str]) -> Set[Path]:
    """Search a directory looking for file patterns."""
    for pattern in file_patterns:
        found_files = list(dir_.glob(pattern))
        if found_files:
            return set(found_files)
    return set()


def confirm_project_root(dir_: Optional[PathOrStr] = None) -> Path:
    """Confirm this is the root dir of the project (the one that has one of the ``ROOT_FILES``)."""
    possible_root_dir = Path(dir_ or Path.cwd())
    root_files = glob_files(possible_root_dir, ROOT_FILES)
    logger.debug(f"Root files found: {root_files}")

    if root_files:
        return next(iter(root_files)).parent

    logger.error(f"No root files found on directory {possible_root_dir}")
    raise QuitComplainingError(Reporter().make_fuss(ProjectViolations.NO_ROOT_DIR))


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
        return confirm_project_root(self._chosen_root)

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

        toml_doc = TomlDoc(path=config_file)
        config_dict = search_json(toml_doc.as_object, TOOL_NITPICK_JMEX, {})
        validation_errors = ToolNitpickSectionSchema().validate(config_dict)
        if not validation_errors:
            return Configuration(config_file, config_dict.get("style", []), config_dict.get("cache", ""))

        # pylint: disable=import-outside-toplevel
        from nitpick.plugins.info import FileInfo

        raise QuitComplainingError(
            Reporter(FileInfo(self, PYPROJECT_TOML)).make_fuss(
                StyleViolations.INVALID_DATA_TOOL_NITPICK,
                flatten_marshmallow_errors(validation_errors),
                section=TOOL_NITPICK_KEY,
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

        minimum_version = search_json(self.style_dict, NITPICK_MINIMUM_VERSION_JMEX, None)
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

    def create_configuration(self, config: Configuration) -> None:
        """Create a configuration file."""
        from nitpick.style import Style  # pylint: disable=import-outside-toplevel

        if config.file:
            doc: TOMLDocument = parse(config.file.read_text())
        else:
            doc = document()
            config.file = self.root / DOT_NITPICK_TOML

        tool_nitpick = table()
        tool_nitpick.add(comment("Generated by the 'nitpick init' command"))
        tool_nitpick.add(comment(f"More info at {READ_THE_DOCS_URL}configuration.html"))
        tool_nitpick.add("style", [Style.get_default_style_url()])
        doc.add(SingleKey(TOOL_NITPICK_KEY, KeyType.Bare), tool_nitpick)

        # config.file will always have a value at this point, but mypy can't see it.
        config.file.write_text(dumps(doc, sort_keys=True))  # type: ignore
