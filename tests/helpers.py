"""Test helpers."""
import os
from pathlib import Path
from pprint import pprint
from textwrap import dedent
from typing import TYPE_CHECKING, List, Set

from _pytest.fixtures import FixtureRequest
from testfixtures import compare

from nitpick.app import NitpickApp
from nitpick.constants import CACHE_DIR_NAME, ERROR_PREFIX, MERGED_STYLE_TOML, NITPICK_STYLE_TOML, PROJECT_NAME
from nitpick.flake8 import NitpickExtension
from nitpick.formats import TOMLFormat
from nitpick.plugins.pre_commit import PreCommitPlugin
from nitpick.plugins.pyproject_toml import PyProjectTomlPlugin
from nitpick.plugins.setup_cfg import SetupCfgPlugin
from nitpick.typedefs import PathOrStr
from tests.conftest import TEMP_PATH

if TYPE_CHECKING:
    from nitpick.typedefs import Flake8Error  # pylint: disable=ungrouped-imports


def assert_conditions(*args):
    """Assert all conditions are True."""
    for arg in args:
        if not arg:
            raise AssertionError()


class ProjectMock:
    """A mocked Python project to help on tests."""

    _original_errors = []  # type: List[Flake8Error]
    _errors = set()  # type: Set[str]

    fixtures_dir = Path(__file__).parent / "fixtures"  # type: Path
    styles_dir = Path(__file__).parent.parent / "styles"  # type: Path

    def __init__(self, pytest_request: FixtureRequest, **kwargs) -> None:
        """Create the root dir and make it the current dir (needed by NitpickChecker)."""
        subdir = "/".join(pytest_request.module.__name__.split(".")[1:])
        caller_function_name = pytest_request.node.name
        self.root_dir = TEMP_PATH / subdir / caller_function_name  # type: Path

        # To make debugging of mock projects easy, each test should not reuse another test directory.
        self.root_dir.mkdir(parents=True)
        self.cache_dir = self.root_dir / CACHE_DIR_NAME / PROJECT_NAME
        self.files_to_lint = []  # type: List[Path]

        if kwargs.get("setup_py", True):
            self.save_file("setup.py", "x = 1")

    def create_symlink(self, link_name: str, target_dir: Path = None, target_file: str = None) -> "ProjectMock":
        """Create a symlink to a target file.

        :param link_name: Link file name.
        :param target_dir: Target directory (default: fixture directory).
        :param target_file: Target file name (default: source file name).
        """
        path = self.root_dir / link_name  # type: Path
        full_source_path = Path(target_dir or self.fixtures_dir) / (target_file or link_name)
        if not full_source_path.exists():
            raise RuntimeError("Source file does not exist: {}".format(full_source_path))
        path.symlink_to(full_source_path)
        if path.suffix == ".py":
            self.files_to_lint.append(path)
        return self

    def flake8(self, offline=False, file_index: int = 0) -> "ProjectMock":
        """Simulate a manual flake8 run.

        - Recreate the global app.
        - Change the working dir to the mocked project root.
        - Lint one of the project files. If no index is provided, use the default file that's always created.
        """
        os.chdir(str(self.root_dir))
        NitpickApp.create_app(offline)

        npc = NitpickExtension(filename=str(self.files_to_lint[file_index]))
        self._original_errors = list(npc.run())

        self._errors = set()
        for flake8_error in self._original_errors:
            line, col, message, class_ = flake8_error
            if not (line == 0 and col == 0 and message.startswith(ERROR_PREFIX) and class_ is NitpickExtension):
                raise AssertionError()
            self._errors.add(message)
        return self

    def save_file(self, file_name: PathOrStr, file_contents: str, lint: bool = None) -> "ProjectMock":
        """Save a file in the root dir with the desired contents.

        Create the parent dirs if the file name contains a slash.

        :param file_name: If it starts with a slash, then it's already a root.
            If it doesn't, then we add the root dir before the partial name.
        :param file_contents: Contents to save in the file.
        :param lint: Should we lint the file or not? Python (.py) files are always linted.
        """
        if str(file_name).startswith("/"):
            path = Path(file_name)  # type: Path
        else:
            path = self.root_dir / file_name
        path.parent.mkdir(parents=True, exist_ok=True)
        if lint or path.suffix == ".py":
            self.files_to_lint.append(path)
        path.write_text(dedent(file_contents).strip())
        return self

    def touch_file(self, file_name: PathOrStr) -> "ProjectMock":
        """Save an empty file (like the ``touch`` command)."""
        return self.save_file(file_name, "")

    def style(self, file_contents: str) -> "ProjectMock":
        """Save the default style file."""
        return self.save_file(NITPICK_STYLE_TOML, file_contents)

    def load_styles(self, *args: PathOrStr) -> "ProjectMock":
        """Load style files from the 'styles' dir, to be used on tests.

        If a style file is modified (file name or contents), tests might break.
        This is a good way to test the style files indirectly.
        """
        for file_name in args:
            style_path = Path(self.styles_dir) / self.ensure_toml_extension(file_name)
            self.named_style(file_name, style_path.read_text())
        return self

    def named_style(self, file_name: PathOrStr, file_contents: str) -> "ProjectMock":
        """Save a style file with a name. Add the .toml extension if needed."""
        return self.save_file(self.ensure_toml_extension(file_name), file_contents)

    @staticmethod
    def ensure_toml_extension(file_name: PathOrStr) -> PathOrStr:
        """Ensure a file name has the .toml extension."""
        return file_name if str(file_name).endswith(".toml") else "{}.toml".format(file_name)

    def setup_cfg(self, file_contents: str) -> "ProjectMock":
        """Save setup.cfg."""
        return self.save_file(SetupCfgPlugin.file_name, file_contents)

    def pyproject_toml(self, file_contents: str) -> "ProjectMock":
        """Save pyproject.toml."""
        return self.save_file(PyProjectTomlPlugin.file_name, file_contents)

    def pre_commit(self, file_contents: str) -> "ProjectMock":
        """Save .pre-commit-config.yaml."""
        return self.save_file(PreCommitPlugin.file_name, file_contents)

    def raise_assertion_error(self, expected_error: str, assertion_message: str = None):
        """Show detailed errors in case of an assertion failure."""
        if expected_error:
            print("Expected error:\n{}".format(expected_error))
        print("\nError count:")
        print(len(self._errors))
        print("\nAll errors:")
        print(sorted(self._errors))
        print("\nAll errors with pprint():")
        pprint(sorted(self._errors), width=150)
        print("\nAll errors with pure print():")
        for error in sorted(self._errors):
            print()
            print(error)
        print("\nProject root:", self.root_dir)
        raise AssertionError(assertion_message or expected_error)

    def _assert_error_count(self, expected_error: str, expected_count: int = None) -> "ProjectMock":
        """Assert the error count is correct."""
        if expected_count is not None:
            actual = len(self._errors)
            if expected_count != actual:
                self.raise_assertion_error(expected_error, "Expected {} errors, got {}".format(expected_count, actual))
        return self

    def assert_errors_contain(self, raw_error: str, expected_count: int = None) -> "ProjectMock":
        """Assert the error is in the error set."""
        expected_error = dedent(raw_error).strip()
        if expected_error not in self._errors:
            self.raise_assertion_error(expected_error)
        self._assert_error_count(expected_error, expected_count)
        return self

    def assert_errors_contain_unordered(self, raw_error: str, expected_count: int = None) -> "ProjectMock":
        """Assert the lines of the error is in the error set, in any order.

        I couldn't find a quick way to guarantee the order of the output with ``ruamel.yaml``.
        """
        # TODO Once there is a way to force some sorting on the YAML output, this method can be removed,
        #  and ``assert_errors_contain()`` can be used again.
        original_expected_error = dedent(raw_error).strip()
        expected_error = original_expected_error.replace("\x1b[0m", "")
        expected_error_lines = set(expected_error.split("\n"))
        for actual_error in self._errors:
            if set(actual_error.replace("\x1b[0m", "").split("\n")) == expected_error_lines:
                self._assert_error_count(raw_error, expected_count)
                return self

        self.raise_assertion_error(original_expected_error)
        return self

    def assert_single_error(self, raw_error: str) -> "ProjectMock":
        """Assert there is only one error."""
        return self.assert_errors_contain(raw_error, 1)

    def assert_no_errors(self) -> "ProjectMock":
        """Assert that there are no errors."""
        if not self._errors:
            return self

        self.raise_assertion_error("")
        return self

    def assert_merged_style(self, toml_string: str):
        """Assert the contents of the merged style file."""
        expected = TOMLFormat(path=self.cache_dir / MERGED_STYLE_TOML)
        actual = TOMLFormat(string=dedent(toml_string))
        compare(expected.as_data, actual.as_data)
