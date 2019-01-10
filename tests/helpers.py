"""Test helpers."""
import os
from pathlib import Path
from typing import List

from flake8_nitpick import Flake8Error, NitpickChecker
from tests.conftest import PROJECT_TEMP_ROOT_PATH


class ProjectMock:
    """A mocked Python project to help on tests."""

    original_errors: List[Flake8Error]
    errors: List[str]

    def __init__(self, project_name: str) -> None:
        """Create the root dir and make it the current dir (needed by NitpickChecker)."""
        self.root: Path = PROJECT_TEMP_ROOT_PATH / project_name
        self.root.mkdir()
        os.chdir(str(self.root))

        self.fixture_dir: Path = Path(__file__).parent / "fixtures"

        # Always create at least one file in the project.
        self.file_paths: List[Path] = []
        self.file_paths.append(self.create_symlink_to_fixture("hello.py"))

    def create_symlink_to_fixture(self, file_name: str) -> Path:
        """Create a symlink to a fixture file inside the temp dir, instead of creating a file."""
        symlink_path: Path = self.root / file_name
        fixture_file = self.fixture_dir / file_name
        if not fixture_file.exists():
            raise RuntimeError(f"Fixture file does not exist: {fixture_file}")
        symlink_path.symlink_to(fixture_file)
        return symlink_path

    def lint(self, file_index: int = 0) -> "ProjectMock":
        """Lint one of the project files. If no index is provided, use the default file that's always created."""
        npc = NitpickChecker(filename=str(self.file_paths[file_index]))
        self.original_errors = list(npc.run())
        self.errors = []
        for flake8_error in self.original_errors:
            line, col, message, class_ = flake8_error
            assert line
            assert col == 0
            assert message
            assert class_ is NitpickChecker
            self.errors.append(message)
        return self
