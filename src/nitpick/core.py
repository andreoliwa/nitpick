"""The Nitpick application and project-related utilities."""
from __future__ import annotations

import itertools
import os
from dataclasses import dataclass
from functools import lru_cache
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING, Iterator

import click
import tomlkit
from autorepr import autorepr
from loguru import logger
from marshmallow_polyfield import PolyField
from more_itertools import always_iterable
from packaging.version import parse as parse_version
from pluggy import PluginManager
from tomlkit import TOMLDocument
from tomlkit.items import KeyType, SingleKey

from nitpick import PROJECT_NAME, fields, plugins
from nitpick.blender import TomlDoc, search_json
from nitpick.constants import (
    CONFIG_FILES,
    CONFIG_TOOL_NITPICK_KEY,
    DOT_NITPICK_TOML,
    JMEX_NITPICK_MINIMUM_VERSION,
    JMEX_TOOL_NITPICK,
    PYTHON_MANAGE_PY,
    PYTHON_PYPROJECT_TOML,
    READ_THE_DOCS_URL,
    ROOT_FILES,
    ROOT_PYTHON_FILES,
)
from nitpick.exceptions import QuitComplainingError
from nitpick.generic import filter_names, glob_files, relative_to_current_dir
from nitpick.plugins.info import FileInfo
from nitpick.schemas import BaseNitpickSchema, flatten_marshmallow_errors, help_message
from nitpick.violations import Fuss, ProjectViolations, Reporter, StyleViolations

if TYPE_CHECKING:
    from nitpick.typedefs import JsonDict, PathOrStr


class Nitpick:
    """The Nitpick API."""

    _allow_init = False

    project: Project

    def __init__(self) -> None:
        if not self._allow_init:
            msg = "This class cannot be instantiated directly. Use Nitpick.singleton().init(...) instead"
            raise TypeError(msg)

        self.offline: bool = False

    @classmethod
    @lru_cache
    def singleton(cls) -> Nitpick:
        """Return a single instance of the class."""
        Nitpick._allow_init = True
        instance = cls()
        Nitpick._allow_init = False
        return instance

    def init(self, project_root: PathOrStr | None = None, offline: bool | None = None) -> Nitpick:
        """Initialize attributes of the singleton."""
        self.project = Project(project_root)

        if offline is not None:
            self.offline = offline

        return self

    def run(self, *partial_names: str, autofix=False) -> Iterator[Fuss]:
        """Run Nitpick.

        :param partial_names: Names of the files to enforce configs for.
        :param autofix: Flag to modify files, if the plugin supports it (default: True).
        :return: Fuss generator.
        """
        Reporter.reset()

        try:
            yield from chain(
                self.project.merge_styles(self.offline),
                self.enforce_present_absent(*partial_names),
                self.enforce_style(*partial_names, autofix=autofix),
            )
        except QuitComplainingError as err:
            yield from err.violations

    def enforce_present_absent(self, *partial_names: str) -> Iterator[Fuss]:
        """Enforce files that should be present or absent.

        :param partial_names: Names of the files to enforce configs for.
        :return: Fuss generator.
        """
        if not self.project:
            return

        for present in (True, False):
            key = "present" if present else "absent"
            logger.debug(f"Enforce {key} files")
            absent = not present
            file_mapping = self.project.nitpick_files_section.get(key, {})
            for filename in filter_names(file_mapping, *partial_names):
                custom_message = file_mapping[filename]
                file_path: Path = self.project.root / filename
                exists = file_path.exists()
                if (present and exists) or (absent and not exists):
                    continue

                reporter = Reporter(FileInfo.create(self.project, filename))

                extra = f": {custom_message}" if custom_message else ""
                violation = ProjectViolations.MISSING_FILE if present else ProjectViolations.FILE_SHOULD_BE_DELETED
                yield reporter.make_fuss(violation, extra=extra)

    def enforce_style(self, *partial_names: str, autofix=True) -> Iterator[Fuss]:
        """Read the merged style and enforce the rules in it.

        1. Get all root keys from the merged style (every key is a filename, except "nitpick").
        2. For each file name, find the plugin(s) that can handle the file.

        :param partial_names: Names of the files to enforce configs for.
        :param autofix: Flag to modify files, if the plugin supports it (default: True).
        :return: Fuss generator.
        """

        # 1.
        for config_key in filter_names(self.project.style_dict, *partial_names):
            config_dict = self.project.style_dict[config_key]
            logger.debug(f"{config_key}: Finding plugins to enforce style")

            # 2.
            info = FileInfo.create(self.project, config_key)
            # pylint: disable=no-member
            for plugin_class in self.project.plugin_manager.hook.can_handle(info=info):
                yield from plugin_class(info, config_dict, autofix).entry_point()

    def configured_files(self, *partial_names: str) -> list[Path]:
        """List of files configured in the Nitpick style.

        Filter only the selected partial names.
        """
        return [Path(self.project.root) / key for key in filter_names(self.project.style_dict, *partial_names)]

    def echo(self, message: str):
        """Echo a message on the terminal, with the relative path at the beginning."""
        relative = relative_to_current_dir(self.project.root)
        if relative:
            relative += os.path.sep
        click.echo(f"{relative}{message}")


def confirm_project_root(dir_: PathOrStr | None = None) -> Path:
    """Confirm this is the root dir of the project (the one that has one of the ``ROOT_FILES``)."""
    possible_root_dir = Path(dir_ or Path.cwd()).resolve()
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
        root_dir.glob(f"*/{PYTHON_MANAGE_PY}"),
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

    error_messages = {"unknown": help_message("Unknown configuration", "configuration.html")}  # noqa: RUF012

    style = PolyField(deserialization_schema_selector=fields.string_or_list_field)
    cache = fields.NonEmptyString()


@dataclass
class Configuration:
    """Configuration read from one of the ``CONFIG_FILES``."""

    file: Path | None
    styles: str | list[str]
    cache: str


class Project:
    """A project to be nitpicked."""

    __repr__ = autorepr(["_chosen_root", "root"])

    _plugin_manager: PluginManager
    _confirmed_root: Path

    def __init__(self, root: PathOrStr | None = None) -> None:
        self._chosen_root = root

        self.style_dict: JsonDict = {}
        self.nitpick_section: JsonDict = {}
        self.nitpick_files_section: JsonDict = {}

    @property
    def root(self) -> Path:
        """Root dir of the project."""
        try:
            root = self._confirmed_root
        except AttributeError:
            root = self._confirmed_root = confirm_project_root(self._chosen_root)
        return root

    @property
    def plugin_manager(self) -> PluginManager:
        """Load all defined plugins."""
        try:
            manager = self._plugin_manager
        except AttributeError:
            manager = self._plugin_manager = PluginManager(PROJECT_NAME)
            manager.add_hookspecs(plugins)
            manager.load_setuptools_entrypoints(PROJECT_NAME)
        return manager

    def read_configuration(self) -> Configuration:
        """Search for a configuration file and validate it against a Marshmallow schema."""
        config_file: Path | None = None
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
        config_dict = search_json(toml_doc.as_object, JMEX_TOOL_NITPICK, {})
        validation_errors = ToolNitpickSectionSchema().validate(config_dict)
        if not validation_errors:
            return Configuration(config_file, config_dict.get("style", []), config_dict.get("cache", ""))

        raise QuitComplainingError(
            Reporter(FileInfo(self, PYTHON_PYPROJECT_TOML)).make_fuss(
                StyleViolations.INVALID_DATA_TOOL_NITPICK,
                flatten_marshmallow_errors(validation_errors),
                section=CONFIG_TOOL_NITPICK_KEY,
            )
        )

    def merge_styles(self, offline: bool) -> Iterator[Fuss]:
        """Merge one or multiple style files."""
        config = self.read_configuration()

        # pylint: disable=import-outside-toplevel
        from nitpick.style import StyleManager

        style = StyleManager(self, offline, config.cache)
        base = config.file.expanduser().resolve().as_uri() if config.file else None
        style_errors = list(style.find_initial_styles(list(always_iterable(config.styles)), base))
        if style_errors:
            raise QuitComplainingError(style_errors)

        self.style_dict = style.merge_toml_dict()

        from nitpick.flake8 import NitpickFlake8Extension

        minimum_version = search_json(self.style_dict, JMEX_NITPICK_MINIMUM_VERSION, None)
        logger.debug(f"Minimum version: {minimum_version}")
        if minimum_version and parse_version(NitpickFlake8Extension.version) < parse_version(minimum_version):
            yield Reporter().make_fuss(
                ProjectViolations.MINIMUM_VERSION,
                project=PROJECT_NAME,
                expected=minimum_version,
                actual=NitpickFlake8Extension.version,
            )

        self.nitpick_section = self.style_dict.get("nitpick", {})
        self.nitpick_files_section = self.nitpick_section.get("files", {})

    def create_configuration(self, config: Configuration, *style_urls: str) -> None:
        """Create a configuration file."""
        from nitpick.style import StyleManager  # pylint: disable=import-outside-toplevel

        if config.file:
            doc: TOMLDocument = tomlkit.parse(config.file.read_text())
        else:
            doc = tomlkit.document()
            config.file = self.root / DOT_NITPICK_TOML

        if not style_urls:
            style_urls = (str(StyleManager.get_default_style_url()),)

        tool_nitpick = tomlkit.table()
        tool_nitpick.add(tomlkit.comment("Generated by the 'nitpick init' command"))
        tool_nitpick.add(tomlkit.comment(f"More info at {READ_THE_DOCS_URL}configuration.html"))
        tool_nitpick.add("style", tomlkit.array([tomlkit.string(url) for url in style_urls]))
        doc.add(SingleKey(CONFIG_TOOL_NITPICK_KEY, KeyType.Bare), tool_nitpick)

        # config.file will always have a value at this point, but mypy can't see it.
        config.file.write_text(tomlkit.dumps(doc, sort_keys=True))
