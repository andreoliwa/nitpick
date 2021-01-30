"""A project to be nitpicked."""
import itertools
import logging
from pathlib import Path
from shutil import rmtree
from typing import Iterable, Optional, Set, Union

from nitpick.constants import CACHE_DIR_NAME, MANAGE_PY, PROJECT_NAME, ROOT_FILES, ROOT_PYTHON_FILES
from nitpick.exceptions import NoPythonFileError, NoRootDirError
from nitpick.typedefs import PathOrStr

LOGGER = logging.getLogger(__name__)


def clear_cache_dir(project_root: Optional[Path]) -> Optional[Path]:  # TODO: add unit tests
    """Clear the cache directory (on the project root or on the current directory)."""
    if not project_root:
        return None
    cache_root: Path = project_root / CACHE_DIR_NAME
    project_cache_dir = cache_root / PROJECT_NAME
    rmtree(str(project_cache_dir), ignore_errors=True)
    return project_cache_dir


class Project:  # pylint: disable=too-few-public-methods
    """A project to be nitpicked."""

    root: Path

    def __init__(self, root: Union[Path, str] = None) -> None:
        self._lazy_root = root

    @staticmethod
    def _find_root() -> Path:  # TODO: add unit tests with tmp_path https://docs.pytest.org/en/stable/tmpdir.html
        """Find the root dir of the Python project (the one that has one of the ``ROOT_FILES``).

        Start from the current working dir.
        """
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
            LOGGER.error("No files found while climbing directory tree from %s", str(starting_file))
            raise NoRootDirError()

        # If multiple roots are found, get the top one (grandparent dir)
        return sorted(root_dirs)[0]

    def find_main_python_file(self) -> Path:  # TODO: add unit tests
        """Find the main Python file in the root dir, the one that will be used to report Flake8 warnings.

        The search order is:
        1. Python files that belong to the root dir of the project (e.g.: ``setup.py``, ``autoapp.py``).
        2. ``manage.py``: they can be on the root or on a subdir (Django projects).
        3. Any other ``*.py`` Python file on the root dir and subdir.
        This avoid long recursions when there is a ``node_modules`` subdir for instance.
        """
        if self._lazy_root:
            self.root = Path(self._lazy_root)
        else:
            self.root = self._find_root()

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
                LOGGER.info("Found the file %s", the_file)
                return Path(the_file)

        raise NoPythonFileError(self.root)


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
