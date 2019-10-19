"""The Nitpick application."""
import itertools
import logging
from pathlib import Path
from shutil import rmtree
from typing import TYPE_CHECKING, List, Set

import click

from nitpick.constants import CACHE_DIR_NAME, ERROR_PREFIX, MANAGE_PY, PROJECT_NAME, ROOT_FILES, ROOT_PYTHON_FILES
from nitpick.exceptions import NitpickError, NoPythonFile, NoRootDir, StyleError
from nitpick.generic import climb_directory_tree
from nitpick.typedefs import Flake8Error

if TYPE_CHECKING:
    from nitpick.config import Config

LOGGER = logging.getLogger(__name__)


class Nitpick:
    """The Nitpick application."""

    _current_app = None  # type: Nitpick

    root_dir = None  # type: Path
    cache_dir = None  # type: Path
    main_python_file = None  # type: Path
    config = None  # type: Config

    def __init__(self) -> None:
        self.init_errors = []  # type: List[NitpickError]
        self.style_errors = []  # type: List[NitpickError]

    @classmethod
    def create_app(cls) -> "Nitpick":
        """Create a single application."""
        # pylint: disable=import-outside-toplevel
        from nitpick.config import Config  # pylint: disable=redefined-outer-name
        from nitpick.files.base import BaseFile

        app = cls()
        cls._current_app = app

        try:
            app.root_dir = app.find_root_dir()
            app.cache_dir = app.clear_cache_dir()

            app.main_python_file = app.find_main_python_file()
            app.config = Config()
            BaseFile.load_fixed_dynamic_classes()
        except (NoRootDir, NoPythonFile) as err:
            app.init_errors.append(err)

        return app

    @classmethod
    def current_app(cls):
        """Get the current app from the stack."""
        return cls._current_app

    @staticmethod
    def find_root_dir() -> Path:
        """Find the root dir of the Python project (the one that has one of the ``ROOT_FILES``).

        Start from the current working dir.
        """
        # pylint: disable=import-outside-toplevel
        from nitpick.files.pyproject_toml import PyProjectTomlFile
        from nitpick.files.setup_cfg import SetupCfgFile

        root_dirs = set()  # type: Set[Path]
        seen = set()  # type: Set[Path]

        starting_file = list(Path.cwd().glob("*"))[0]
        starting_dir = Path(starting_file).parent.absolute()
        while True:
            project_files = climb_directory_tree(
                starting_dir, ROOT_FILES + (PyProjectTomlFile.file_name, SetupCfgFile.file_name)
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

    def clear_cache_dir(self) -> Path:
        """Clear the cache directory (on the project root or on the current directory)."""
        cache_root = self.root_dir / CACHE_DIR_NAME  # type: Path
        cache_dir = cache_root / PROJECT_NAME
        rmtree(str(cache_dir), ignore_errors=True)
        return cache_dir

    def find_main_python_file(self) -> Path:
        """Find the main Python file in the root dir, the one that will be used to report Flake8 warnings.

        The search order is:
        1. Python files that belong to the root dir of the project (e.g.: ``setup.py``, ``autoapp.py``).
        2. ``manage.py``: they can be on the root or on a subdir (Django projects).
        3. Any other ``*.py`` Python file.
        """
        for the_file in itertools.chain(
            [self.root_dir / root_file for root_file in ROOT_PYTHON_FILES],
            self.root_dir.glob("*/{}".format(MANAGE_PY)),
            self.root_dir.glob("*/*.py"),
        ):
            if the_file.exists():
                LOGGER.info("Found the file %s", the_file)
                return Path(the_file)

        raise NoPythonFile(self.root_dir)

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

        from nitpick.plugin import NitpickChecker  # pylint: disable=import-outside-toplevel

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
            NitpickChecker,
        )

    def add_style_error(self, file_name: str, message: str, invalid_data: str = None) -> None:
        """Add a style error to the internal list."""
        err = StyleError(file_name)
        err.message = "File {} has an incorrect style. {}".format(file_name, message)
        if invalid_data:
            err.suggestion = invalid_data
        self.style_errors.append(err)
