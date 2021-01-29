"""The Nitpick application."""
import itertools
import logging
from functools import lru_cache
from pathlib import Path
from shutil import rmtree
from typing import TYPE_CHECKING, Optional, Set

import click
import pluggy
from pluggy import PluginManager
from pydantic.dataclasses import dataclass

from nitpick import plugins
from nitpick.constants import CACHE_DIR_NAME, MANAGE_PY, PROJECT_NAME, ROOT_FILES, ROOT_PYTHON_FILES
from nitpick.exceptions import NoPythonFileError, NoRootDirError
from nitpick.generic import climb_directory_tree
from nitpick.typedefs import mypy_property

if TYPE_CHECKING:
    from nitpick.config import Config

LOGGER = logging.getLogger(__name__)


# TODO: add tests for this function with tmp_path https://docs.pytest.org/en/stable/tmpdir.html
def find_project_root() -> Path:
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
        raise NoRootDirError()

    # If multiple roots are found, get the top one (grandparent dir)
    return sorted(root_dirs)[0]


def find_main_python_file(project_root: Path) -> Path:  # TODO: add unit tests
    """Find the main Python file in the root dir, the one that will be used to report Flake8 warnings.

    The search order is:
    1. Python files that belong to the root dir of the project (e.g.: ``setup.py``, ``autoapp.py``).
    2. ``manage.py``: they can be on the root or on a subdir (Django projects).
    3. Any other ``*.py`` Python file on the root dir and subdir.
    This avoid long recursions when there is a ``node_modules`` subdir for instance.
    """
    for the_file in itertools.chain(
        # 1.
        [project_root / root_file for root_file in ROOT_PYTHON_FILES],
        # 2.
        project_root.glob("*/{}".format(MANAGE_PY)),
        # 3.
        project_root.glob("*.py"),
        project_root.glob("*/*.py"),
    ):
        if the_file.exists():
            LOGGER.info("Found the file %s", the_file)
            return Path(the_file)

    raise NoPythonFileError(project_root)


def clear_cache_dir(project_root: Path) -> Path:  # TODO: add unit tests
    """Clear the cache directory (on the project root or on the current directory)."""
    cache_root: Path = project_root / CACHE_DIR_NAME
    project_cache_dir = cache_root / PROJECT_NAME
    rmtree(str(project_cache_dir), ignore_errors=True)
    return project_cache_dir


class Nitpick:
    """The Nitpick API."""

    _allow_init = False

    @dataclass(eq=False)
    class Options:
        """Options."""

        project_root: Optional[Path] = None
        offline: bool = False
        check: bool = False

    def __init__(self):
        if not self._allow_init:
            raise TypeError("This class cannot be instantiated directly. Call Nitpick.create() instead")
        self.options: Nitpick.Options = Nitpick.Options()

    @classmethod
    @lru_cache()
    def create(cls) -> "Nitpick":
        """Return a single instance of the class."""
        Nitpick._allow_init = True
        instance = cls()
        Nitpick._allow_init = False
        return instance

    def cli_debug_info(self):
        """Display debug config on the CLI."""
        click.echo(f"Offline? {self.options.offline}")
        click.echo(f"Check only? {self.options.check}")
        click.echo(f"Root dir: {self.project_root}")
        click.echo(f"Cache dir: {self.cache_dir}")

    @mypy_property
    @lru_cache()
    def project_root(self) -> Path:
        """Root dir of the project."""
        return find_project_root()

    @mypy_property
    @lru_cache()
    def cache_dir(self) -> Path:
        """Clear the cache directory (on the project root or on the current directory)."""
        return clear_cache_dir(self.project_root)

    @mypy_property
    @lru_cache()
    def main_python_file(self) -> Path:
        """Find the main Python file in the root dir, the one that will be used to report Flake8 warnings."""
        return find_main_python_file(self.project_root)

    @mypy_property
    @lru_cache()
    def config(self) -> "Config":
        """Configuration."""
        from nitpick.config import Config  # pylint: disable=import-outside-toplevel

        return Config(self.project_root, self.plugin_manager)

    @mypy_property
    @lru_cache()
    def plugin_manager(self) -> PluginManager:
        """Load all defined plugins."""
        plugin_manager = pluggy.PluginManager(PROJECT_NAME)
        plugin_manager.add_hookspecs(plugins)
        plugin_manager.load_setuptools_entrypoints(PROJECT_NAME)
        return plugin_manager
