"""Test helpers."""
import os
from pathlib import Path
from pprint import pprint
from typing import List, Set

from _pytest.fixtures import FixtureRequest

from flake8_nitpick import (
    ERROR_PREFIX,
    NITPICK_STYLE_TOML,
    Flake8Error,
    NitpickChecker,
    PreCommitChecker,
    PyProjectTomlChecker,
    SetupCfgChecker,
)
from tests.conftest import TEMP_ROOT_PATH


class ProjectMock:
    """A mocked Python project to help on tests."""

    original_errors: List[Flake8Error]
    errors: Set[str]

    def __init__(self, pytest_request: FixtureRequest, **kwargs) -> None:
        """Create the root dir and make it the current dir (needed by NitpickChecker)."""
        self.root_dir: Path = TEMP_ROOT_PATH / pytest_request.node.name
        self.root_dir.mkdir()
        os.chdir(str(self.root_dir))

        self.fixture_dir: Path = Path(__file__).parent / "fixtures"

        self.files_to_lint: List[Path] = []

        if kwargs.get("setup_py", True):
            self.save_file("setup.py", "x = 1")
        if kwargs.get("pyproject_toml", True):
            self.pyproject_toml("")

    def create_symlink_to_fixture(self, file_name: str) -> "ProjectMock":
        """Create a symlink to a fixture file inside the temp dir, instead of creating a file."""
        path: Path = self.root_dir / file_name
        fixture_file = self.fixture_dir / file_name
        if not fixture_file.exists():
            raise RuntimeError(f"Fixture file does not exist: {fixture_file}")
        path.symlink_to(fixture_file)
        if path.suffix == ".py":
            self.files_to_lint.append(path)
        return self

    def lint(self, file_index: int = 0) -> "ProjectMock":
        """Lint one of the project files. If no index is provided, use the default file that's always created."""
        npc = NitpickChecker(filename=str(self.files_to_lint[file_index]))
        self.original_errors = list(npc.run())
        self.errors = set()
        for flake8_error in self.original_errors:
            line, col, message, class_ = flake8_error
            assert line == 1
            assert col == 0
            assert message.startswith(ERROR_PREFIX)
            assert class_ is NitpickChecker
            self.errors.add(message)
        return self

    def save_file(self, file_name: str, file_contents: str, lint: bool = None) -> "ProjectMock":
        """Save a file in the root dir with the desired contents."""
        path: Path = self.root_dir / file_name
        if lint or path.suffix == ".py":
            self.files_to_lint.append(path)
        path.write_text(file_contents)
        return self

    def style(self, file_contents: str) -> "ProjectMock":
        """Save the default style file."""
        return self.save_file(NITPICK_STYLE_TOML, file_contents)

    def setup_cfg(self, file_contents: str) -> "ProjectMock":
        """Save setup.cfg."""
        return self.save_file(SetupCfgChecker.file_name, file_contents)

    def pyproject_toml(self, file_contents: str):
        """Save pyproject.toml."""
        return self.save_file(PyProjectTomlChecker.file_name, file_contents)

    def pre_commit(self, file_contents: str):
        """Save .pre-commit-config.yaml."""
        return self.save_file(PreCommitChecker.file_name, file_contents)

    def assert_errors_contain(self, error: str) -> None:
        """Assert the error is in the error set."""
        if error in self.errors:
            return

        print(f"Expected error:\n{error}")
        print("\nAll errors:")
        pprint(self.errors, width=150)
        assert False
