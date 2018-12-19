"""Main package."""
from typing import Optional

import attr
from pathlib import Path

import toml

from flake8_nitpick.__version__ import __version__

NITPICK_TOML = "nitpick.toml"


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

        project.load_config()
        for msg in project.check_files():
            yield msg
        return []


class PythonProject:
    """Class to represent a Python project."""

    ROOT_FILES = ("setup.cfg", "setup.py", "Pipfile", "manage.py")

    config: dict

    def __init__(self, python_file: str) -> None:
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
        return None

    def is_main_file(self):
        """Return True if the current Python file is a main file.

        We will use this to display the warnings only once.
        """
        return self.root_dir and self.root_dir == self.python_file.parent

    def load_config(self):
        """Load configuration from a TOML file."""
        self.config = toml.load(str(self.root_dir / NITPICK_TOML))

    def check_files(self):
        """Check the files section of the .toml file."""
        if "files" not in self.config:
            yield (1, 0, f"NIP100 Missing 'files' section in {NITPICK_TOML}", type(self))
            return

        for file_name, should_exist in self.config["files"].items():
            one_file: Path = self.root_dir / file_name
            if should_exist and not one_file.exists():
                yield (1, 0, f"NIP101 Missing file {file_name}", type(self))
            elif not should_exist and one_file.exists():
                yield (1, 0, f"NIP102 File {file_name} should be deleted", type(self))
