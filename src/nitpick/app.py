"""The Nitpick application."""
import itertools
import logging
import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from shutil import rmtree
from typing import TYPE_CHECKING, List, Set

import click
import pluggy
from pluggy import PluginManager

from nitpick import plugins
from nitpick.constants import (
    CACHE_DIR_NAME,
    ERROR_PREFIX,
    MANAGE_PY,
    MISSING,
    PROJECT_NAME,
    ROOT_FILES,
    ROOT_PYTHON_FILES,
)
from nitpick.exceptions import NitpickError, NoPythonFile, NoRootDir, StyleError
from nitpick.generic import Borg, climb_directory_tree
from nitpick.mixin import NitpickMixin
from nitpick.typedefs import Flake8Error, YieldFlake8Error

if TYPE_CHECKING:
    from nitpick.config import Config

LOGGER = logging.getLogger(__name__)


# TODO: add tests for this function with tmp_path https://docs.pytest.org/en/stable/tmpdir.html
def find_root_dir() -> Path:
    """Find the root dir of the Python project (the one that has one of the ``ROOT_FILES``).

    Start from the current working dir.
    """
    # pylint: disable=import-outside-toplevel
    from nitpick.plugins.pyproject_toml import PyProjectTomlPlugin
    from nitpick.plugins.setup_cfg import SetupCfgPlugin

    root_dirs = set()  # type: Set[Path]
    seen = set()  # type: Set[Path]

    all_files = list(Path.cwd().glob("*"))
    # Don't fail if the current dir is empty
    starting_file = str(all_files[0]) if all_files else ""
    starting_dir = Path(starting_file).parent.absolute()
    while True:
        project_files = climb_directory_tree(
            starting_dir, ROOT_FILES + (PyProjectTomlPlugin.file_name, SetupCfgPlugin.file_name)
        )
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
        LOGGER.error("No files found while climbing directory tree from %s", str(starting_file))
        raise NoRootDir()

    # If multiple roots are found, get the top one (grandparent dir)
    return sorted(root_dirs)[0]


def find_main_python_file(root_dir: Path) -> Path:  # TODO: add unit tests
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
        root_dir.glob("*/{}".format(MANAGE_PY)),
        # 3.
        root_dir.glob("*.py"),
        root_dir.glob("*/*.py"),
    ):
        if the_file.exists():
            LOGGER.info("Found the file %s", the_file)
            return Path(the_file)

    raise NoPythonFile(root_dir)


def load_plugins() -> PluginManager:
    """Load all defined plugins."""
    plugin_manager = pluggy.PluginManager(PROJECT_NAME)
    plugin_manager.add_hookspecs(plugins)
    plugin_manager.load_setuptools_entrypoints(PROJECT_NAME)
    return plugin_manager


# FIXME[AA]: move methods to Nitpick after removing NitpickApp
class _TransitionMixin(NitpickMixin):  # pylint: disable=too-few-public-methods
    """Mixin class to transition from NitpickApp (flake8) to Nitpick (CLI)."""

    root_dir: Path
    style_errors: List[NitpickError] = []

    def clear_cache_dir(self) -> Path:
        """Clear the cache directory (on the project root or on the current directory)."""
        cache_root = self.root_dir / CACHE_DIR_NAME  # type: Path
        cache_dir = cache_root / PROJECT_NAME
        rmtree(str(cache_dir), ignore_errors=True)
        return cache_dir

    def check_files(self, present: bool) -> YieldFlake8Error:
        """Check files that should be present or absent."""
        key = "present" if present else "absent"
        message = "exist" if present else "be deleted"
        absent = not present
        for file_name, extra_message in NitpickApp.current().config.nitpick_files_section.get(key, {}).items():
            file_path = NitpickApp.current().root_dir / file_name  # type: Path
            exists = file_path.exists()
            if (present and exists) or (absent and not exists):
                continue

            full_message = "File {} should {}".format(file_name, message)
            if extra_message:
                full_message += ": {}".format(extra_message)

            yield self.flake8_error(3 if present else 4, full_message)

    def add_style_error(self, file_name: str, message: str, invalid_data: str = None) -> None:
        """Add a style error to the internal list."""
        err = StyleError(file_name)
        err.message = "File {} has an incorrect style. {}".format(file_name, message)
        if invalid_data:
            err.suggestion = invalid_data
        self.style_errors.append(err)


# FIXME[AA]: move all attributes+methods to Nitpick or _TransitionMixin, then remove this class
class NitpickApp(_TransitionMixin):  # pylint: disable=too-many-instance-attributes
    """The Nitpick application."""

    cache_dir = None  # type: Path
    main_python_file = None  # type: Path
    config = None  # type: Config
    plugin_manager = None  # type: PluginManager

    def __init__(self) -> None:
        self.init_errors = []  # type: List[NitpickError]
        self.style_errors = []  # type: List[NitpickError]

        self.offline = False

    @classmethod
    def create_app(cls, offline=False) -> "NitpickApp":
        """Create a single application."""
        # pylint: disable=import-outside-toplevel
        from nitpick.config import Config  # pylint: disable=redefined-outer-name
        from nitpick.plugins.base import NitpickPlugin

        app = cls.current()
        app.offline = offline

        try:
            app.root_dir = find_root_dir()
            app.cache_dir = app.clear_cache_dir()

            app.main_python_file = find_main_python_file(app.root_dir)
            app.config = Config()
            app.plugin_manager = load_plugins()
            NitpickPlugin.load_fixed_dynamic_classes(app.plugin_manager)
        except (NoRootDir, NoPythonFile) as err:
            app.init_errors.append(err)

        return app

    @classmethod
    @lru_cache(typed=True)
    def current(cls) -> "NitpickApp":
        """Return a single instance of the class (singleton)."""
        return cls()

    @staticmethod
    def as_flake8_warning(nitpick_error: NitpickError) -> Flake8Error:
        """Return a flake8 error as a tuple."""
        joined_number = (
            nitpick_error.error_base_number + nitpick_error.number
            if nitpick_error.add_to_base_number
            else nitpick_error.number
        )
        suggestion_with_newline = (
            click.style("\n{}".format(nitpick_error.suggestion.rstrip()), fg="green")
            if nitpick_error.suggestion
            else ""
        )

        from nitpick.flake8 import NitpickExtension  # pylint: disable=import-outside-toplevel

        return (
            0,
            0,
            "{}{:03d} {}{}{}".format(
                ERROR_PREFIX,
                joined_number,
                nitpick_error.error_prefix,
                nitpick_error.message.rstrip(),
                suggestion_with_newline,
            ),
            NitpickExtension,
        )

    def add_style_error(self, file_name: str, message: str, invalid_data: str = None) -> None:
        """Add a style error to the internal list."""
        err = StyleError(file_name)
        err.message = "File {} has an incorrect style. {}".format(file_name, message)
        if invalid_data:
            err.suggestion = invalid_data
        self.style_errors.append(err)

    @classmethod
    def format_flag(cls, flag: Enum) -> str:
        """Format the name of a flag to be used on the CLI."""
        return "--{}-{}".format(PROJECT_NAME, flag.name.lower().replace("_", "-"))

    @classmethod
    def format_env(cls, flag: Enum) -> str:
        """Format the name of an environment variable."""
        return "{}_{}".format(PROJECT_NAME.upper(), flag.name.upper())

    @classmethod
    def get_env(cls, flag: Enum) -> str:
        """Get the value of an environment variable."""
        return os.environ.get(cls.format_env(flag), "")


class Nitpick(Borg, _TransitionMixin):
    """The Nitpick API."""

    offline: bool
    check: bool

    def __init__(self, offline=MISSING, check=MISSING):
        super().__init__()
        first_instance: bool = not hasattr(self, "offline")

        self._init_attribute("offline", offline, False)
        self._init_attribute("check", check, False)

        # FIXME[AA]: call these methods on demand with lru_cache, when called the first time?
        if first_instance:
            # pylint: disable=import-outside-toplevel
            from nitpick.plugins.base import NitpickPlugin

            self.root_dir = find_root_dir()
            self.cache_dir = self.clear_cache_dir()
            self.main_python_file = find_main_python_file(self.root_dir)
            self.plugin_manager = load_plugins()
            NitpickPlugin.load_fixed_dynamic_classes(self.plugin_manager)

    def cli_debug_info(self):
        """Display debug config on the CLI."""
        click.echo(f"Offline? {self.offline}")
        click.echo(f"Check only? {self.check}")
        click.echo(f"Root dir: {self.root_dir}")
        click.echo(f"Cache dir: {self.cache_dir}")
