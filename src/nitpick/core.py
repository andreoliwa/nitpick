"""The Nitpick application and project-related utilities."""

from __future__ import annotations

import itertools
import os
from dataclasses import dataclass
from functools import lru_cache
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Iterator

import click
import tomlkit
from autorepr import autorepr
from identify import identify
from loguru import logger
from marshmallow_polyfield import PolyField
from more_itertools import always_iterable
from packaging.version import parse as parse_version
from pluggy import PluginManager
from tomlkit import items

from nitpick import fields, plugins, tomlkit_ext
from nitpick.blender import search_json
from nitpick.constants import (
    ANY_BUILTIN_STYLE,
    CONFIG_FILES,
    CONFIG_KEY_IGNORE_STYLES,
    CONFIG_KEY_STYLE,
    CONFIG_KEY_TOOL,
    CONFIG_TOOL_NITPICK_KEY,
    DOT_NITPICK_TOML,
    JMEX_NITPICK_MINIMUM_VERSION,
    PROJECT_NAME,
    PYTHON_MANAGE_PY,
    PYTHON_PYPROJECT_TOML,
    ROOT_FILES,
    ROOT_PYTHON_FILES,
)
from nitpick.exceptions import QuitComplainingError
from nitpick.generic import filter_names, glob_files, glob_non_ignored_files, relative_to_current_dir
from nitpick.plugins.info import FileInfo
from nitpick.schemas import BaseNitpickSchema, flatten_marshmallow_errors, help_message
from nitpick.style import (
    BuiltinStyle,
    StyleManager,
    builtin_styles,
)
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
    """Validation schema for the ``[tool.nitpick]`` table on ``pyproject.toml``."""

    error_messages = {"unknown": help_message("Unknown configuration", "configuration.html")}  # noqa: RUF012

    style = PolyField(deserialization_schema_selector=fields.string_or_list_field)
    cache = fields.NonEmptyString()
    ignore_styles = fields.List(fields.NonEmptyString())


@dataclass
class Configuration:
    """Configuration read from the ``[tool.nitpick]`` table from one of the ``CONFIG_FILES``."""

    file: Path
    doc: tomlkit.TOMLDocument
    table: items.Table
    styles: items.Array
    dont_suggest: items.Array
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

    def config_file_or_default(self) -> Path:
        """Return a config file if found, or the default one."""
        config_file = self.config_file()
        if config_file:
            return config_file
        return self.root / DOT_NITPICK_TOML

    def config_file(self) -> Path | None:
        """Determine which config file to use."""
        found: Path | None = None
        for possible in CONFIG_FILES:
            existing: Path = self.root / possible
            if not existing.exists():
                continue

            if not found:
                logger.info(f"Config file: reading from {existing}")
                found = existing
            else:
                logger.warning(f"Config file: ignoring existing {existing}")

        if not found:
            logger.warning("Config file: none found")

        return found

    def read_configuration(self) -> Configuration:
        """Return the ``[tool.nitpick]`` table from the configuration file.

        Optionally, validate it against a Marshmallow schema.
        """
        config_file = self.config_file_or_default()
        doc = tomlkit_ext.load(config_file)
        table: items.Table | None = doc.get(CONFIG_TOOL_NITPICK_KEY)
        if not table:
            super_table = tomlkit.table(True)
            nitpick_table = tomlkit.table()
            nitpick_table.update({CONFIG_KEY_STYLE: []})
            super_table.append(PROJECT_NAME, nitpick_table)
            doc.append(CONFIG_KEY_TOOL, super_table)
            table = doc.get(CONFIG_TOOL_NITPICK_KEY)

        validation_errors = ToolNitpickSectionSchema().validate(table)
        if validation_errors:
            raise QuitComplainingError(
                Reporter(FileInfo(self, PYTHON_PYPROJECT_TOML)).make_fuss(
                    StyleViolations.INVALID_DATA_TOOL_NITPICK,
                    flatten_marshmallow_errors(validation_errors),
                    section=CONFIG_TOOL_NITPICK_KEY,
                )
            )

        existing_styles: items.Array = table.get(CONFIG_KEY_STYLE)
        if existing_styles is None:
            existing_styles = tomlkit.array()
            table.add(CONFIG_KEY_STYLE, existing_styles)

        ignored_styles: items.Array = table.get(CONFIG_KEY_IGNORE_STYLES)
        if ignored_styles is None:
            ignored_styles = tomlkit.array()

        return Configuration(config_file, doc, table, existing_styles, ignored_styles, table.get("cache", ""))

    def merge_styles(self, offline: bool) -> Iterator[Fuss]:
        """Merge one or multiple style files."""
        config = self.read_configuration()
        style = StyleManager(self, offline, config.cache)
        base = config.file.expanduser().resolve().as_uri()
        style_errors = list(style.find_initial_styles(list(always_iterable(config.styles)), base))
        if style_errors:
            raise QuitComplainingError(style_errors)

        self.style_dict = style.merge_toml_dict()

        from nitpick.flake8 import NitpickFlake8Extension  # pylint: disable=import-outside-toplevel  # noqa: PLC0415

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

    def suggest_styles(self, library_path_str: PathOrStr | None) -> list[str]:
        """Suggest styles based on the files in the project root (skipping Git ignored files)."""
        all_tags: set[str] = {ANY_BUILTIN_STYLE}
        for project_file_path in glob_non_ignored_files(self.root):
            all_tags.update(identify.tags_from_path(str(project_file_path)))

        if library_path_str:
            library_dir = Path(library_path_str)
            all_styles: Iterable[Path] = library_dir.glob("**/*.toml")
        else:
            library_dir = None
            all_styles = builtin_styles()

        suggested_styles: set[str] = set()
        for style_path in all_styles:
            style = BuiltinStyle.from_path(style_path, library_dir)
            if style.identify_tag in all_tags:
                suggested_styles.add(style.formatted)
        return sorted(suggested_styles)
