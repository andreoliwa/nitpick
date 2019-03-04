"""Test helpers."""
import os
from pathlib import Path
from pprint import pprint
from textwrap import dedent
from typing import List, Set

from _pytest.fixtures import FixtureRequest

from flake8_nitpick.constants import ERROR_PREFIX, NITPICK_STYLE_TOML
from flake8_nitpick.files.pre_commit import PreCommitFile
from flake8_nitpick.files.pyproject_toml import PyProjectTomlFile
from flake8_nitpick.files.setup_cfg import SetupCfgFile
from flake8_nitpick.plugin import NitpickChecker
from flake8_nitpick.types import Flake8Error, PathOrStr
from tests.conftest import TEMP_ROOT_PATH


class ProjectMock:
    """A mocked Python project to help on tests."""

    original_errors: List[Flake8Error]
    errors: Set[str]

    fixture_dir: Path = Path(__file__).parent / "fixtures"

    def __init__(self, pytest_request: FixtureRequest, **kwargs) -> None:
        """Create the root dir and make it the current dir (needed by NitpickChecker)."""
        self.root_dir: Path = TEMP_ROOT_PATH / pytest_request.node.name
        self.root_dir.mkdir()
        os.chdir(str(self.root_dir))

        self.files_to_lint: List[Path] = []

        if kwargs.get("setup_py", True):
            self.save_file("setup.py", "x = 1")

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

    def save_file(self, file_name: PathOrStr, file_contents: str, lint: bool = None) -> "ProjectMock":
        """Save a file in the root dir with the desired contents."""
        path: Path = self.root_dir / file_name
        if lint or path.suffix == ".py":
            self.files_to_lint.append(path)
        path.write_text(dedent(file_contents))
        return self

    def touch_file(self, file_name: PathOrStr):
        """Save an empty file (like the ``touch`` command)."""
        return self.save_file(file_name, "")

    def style(self, file_contents: str) -> "ProjectMock":
        """Save the default style file."""
        return self.save_file(NITPICK_STYLE_TOML, file_contents)

    def named_style(self, file_name: PathOrStr, file_contents: str) -> "ProjectMock":
        """Save a style file with a name. Add the .toml extension if needed."""
        clean_file_name = file_name if str(file_name).endswith(".toml") else f"{file_name}.toml"
        return self.save_file(clean_file_name, file_contents)

    def setup_cfg(self, file_contents: str) -> "ProjectMock":
        """Save setup.cfg."""
        return self.save_file(SetupCfgFile.file_name, file_contents)

    def pyproject_toml(self, file_contents: str):
        """Save pyproject.toml."""
        return self.save_file(PyProjectTomlFile.file_name, file_contents)

    def pre_commit(self, file_contents: str):
        """Save .pre-commit-config.yaml."""
        return self.save_file(PreCommitFile.file_name, file_contents)

    def assert_errors_contain(self, raw_error: str) -> "ProjectMock":
        """Assert the error is in the error set."""
        error = dedent(raw_error).strip()
        if error in self.errors:
            return self

        print(f"Expected error:\n{error}")
        print("\nAll errors:")
        print(sorted(self.errors))
        print("\nAll errors (pprint):")
        pprint(sorted(self.errors), width=150)
        assert False
