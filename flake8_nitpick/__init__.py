"""Main package."""
from typing import Optional

import attr
import os
from pathlib import Path
from flake8_nitpick.__version__ import __version__
from functools import lru_cache


@attr.s
class NitpickChecker:
    """Main plugin class."""

    name = "flake8-nitpick"
    version = __version__

    tree = attr.ib(default=None)
    filename = attr.ib(default="(none)")

    def run(self):
        """Run the check plugin."""
        project = PythonProject(self.filename)
        if not project.is_main_file():
            # Only if this Python file is the main one.
            return

        pyproject_toml: Path = self.root() / "pyproject.toml"
        if not pyproject_toml.exists():
            yield (1, 0, "NIP100 Missing pyproject.toml", type(self))

    @staticmethod
    @lru_cache()
    def root() -> Path:
        return Path(os.curdir).resolve()


class PythonProject:
    """Class to represent a Python project."""

    ROOT_FILES = ("setup.cfg", "setup.py")  # , "Pipfile", "xmanage.py")

    def __init__(self, python_file: str):
        """Init the instance."""
        self.root_dir: Optional[Path] = self._find_root_dir(python_file)
        self.python_file: Path = Path(python_file).resolve()

    def _find_root_dir(self, python_file: str) -> Optional[Path]:
        current_dir: Path = Path(python_file).resolve().parent
        while current_dir.exists():
            for root_file in self.ROOT_FILES:
                found_files = list(current_dir.glob(root_file))
                if found_files:
                    return found_files[0].parent
            current_dir = current_dir.parent
            if current_dir.root == str(current_dir):
                return None

    def is_main_file(self):
        """Return True if the current Python file is a main file.

        We will use this to display the warnings only once.
        """
        return self.root_dir and self.root_dir == self.python_file.parent
