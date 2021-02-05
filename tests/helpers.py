"""Test helpers."""
import os
from pathlib import Path
from pprint import pprint
from textwrap import dedent
from typing import List, Set

from _pytest.fixtures import FixtureRequest
from testfixtures import compare

from nitpick.constants import (
    CACHE_DIR_NAME,
    FLAKE8_PREFIX,
    MERGED_STYLE_TOML,
    NITPICK_STYLE_TOML,
    PROJECT_NAME,
    PYPROJECT_TOML,
    SETUP_CFG,
)
from nitpick.core import Nitpick
from nitpick.flake8 import NitpickFlake8Extension
from nitpick.formats import TOMLFormat
from nitpick.plugins.pre_commit import PreCommitPlugin
from nitpick.typedefs import Flake8Error, PathOrStr
from nitpick.violations import Fuss
from tests.conftest import TEMP_PATH


def assert_conditions(*args):
    """Assert all conditions are True."""
    for arg in args:
        if not arg:
            raise AssertionError()


class ProjectMock:
    """A mocked Python project to help on tests."""

    # TODO: use Python 3.6 type annotations
    fixtures_dir: Path = Path(__file__).parent / "fixtures"
    styles_dir: Path = Path(__file__).parent.parent / "styles"

    def __init__(self, pytest_request: FixtureRequest, **kwargs) -> None:
        """Create the root dir and make it the current dir (needed by NitpickChecker)."""
        self._fusses: List[Fuss] = []
        self._flake8_errors: List[Flake8Error] = []
        self._flake8_errors_as_string: Set[str] = set()

        subdir = "/".join(pytest_request.module.__name__.split(".")[1:])
        caller_function_name = pytest_request.node.name
        # TODO: use tmp_path instead of self.root_dir
        self.root_dir: Path = TEMP_PATH / subdir / caller_function_name

        # To make debugging of mock projects easy, each test should not reuse another test directory.
        self.root_dir.mkdir(parents=True)
        self.cache_dir = self.root_dir / CACHE_DIR_NAME / PROJECT_NAME
        self.files_to_lint: List[Path] = []

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

    def simulate_run(self, offline=False, call_api=True) -> "ProjectMock":
        """Simulate a manual flake8 run and using the API.

        - Clear the singleton cache.
        - Recreate the global app.
        - Change the working dir to the mocked project root.
        - Lint one of the project files. If no index is provided, use the default file that's always created.
        """
        Nitpick.singleton.cache_clear()
        os.chdir(str(self.root_dir))
        nit = Nitpick.singleton().init(offline=offline)
        if call_api:
            self._fusses = list(nit.run())

        npc = NitpickFlake8Extension(filename=str(self.files_to_lint[0]))
        self._flake8_errors = list(npc.run())

        self._flake8_errors_as_string = set()
        for line, col, message, class_ in self._flake8_errors:
            if not (line == 0 and col == 0 and message.startswith(FLAKE8_PREFIX) and class_ is NitpickFlake8Extension):
                raise AssertionError()
            self._flake8_errors_as_string.add(message)
        return self

    def save_file(self, filename: PathOrStr, file_contents: str, lint: bool = None) -> "ProjectMock":
        """Save a file in the root dir with the desired contents.

        Create the parent dirs if the file name contains a slash.

        :param filename: If it starts with a slash, then it's already a root.
            If it doesn't, then we add the root dir before the partial name.
        :param file_contents: Contents to save in the file.
        :param lint: Should we lint the file or not? Python (.py) files are always linted.
        """
        if str(filename).startswith("/"):
            path = Path(filename)  # type: Path
        else:
            path = self.root_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        if lint or path.suffix == ".py":
            self.files_to_lint.append(path)
        path.write_text(dedent(file_contents).strip())
        return self

    def touch_file(self, filename: PathOrStr) -> "ProjectMock":
        """Save an empty file (like the ``touch`` command)."""
        return self.save_file(filename, "")

    def style(self, file_contents: str) -> "ProjectMock":
        """Save the default style file."""
        return self.save_file(NITPICK_STYLE_TOML, file_contents)

    def load_styles(self, *args: PathOrStr) -> "ProjectMock":
        """Load style files from the 'styles' dir, to be used on tests.

        If a style file is modified (file name or contents), tests might break.
        This is a good way to test the style files indirectly.
        """
        for filename in args:
            style_path = Path(self.styles_dir) / self.ensure_toml_extension(filename)
            self.named_style(filename, style_path.read_text())
        return self

    def named_style(self, filename: PathOrStr, file_contents: str) -> "ProjectMock":
        """Save a style file with a name. Add the .toml extension if needed."""
        return self.save_file(self.ensure_toml_extension(filename), file_contents)

    @staticmethod
    def ensure_toml_extension(filename: PathOrStr) -> PathOrStr:
        """Ensure a file name has the .toml extension."""
        return filename if str(filename).endswith(".toml") else "{}.toml".format(filename)

    def setup_cfg(self, file_contents: str) -> "ProjectMock":
        """Save setup.cfg."""
        return self.save_file(SETUP_CFG, file_contents)

    def pyproject_toml(self, file_contents: str) -> "ProjectMock":
        """Save pyproject.toml."""
        return self.save_file(PYPROJECT_TOML, file_contents)

    def pre_commit(self, file_contents: str) -> "ProjectMock":
        """Save .pre-commit-config.yaml."""
        return self.save_file(PreCommitPlugin.filename, file_contents)

    def raise_assertion_error(self, expected_error: str, assertion_message: str = None):
        """Show detailed errors in case of an assertion failure."""
        if expected_error:
            print(f"Expected error:\n<<<{expected_error}>>>")
        print("\nError count:")
        print(len(self._flake8_errors_as_string))
        print("\nAll errors:")
        print(sorted(self._flake8_errors_as_string))
        print("\nAll errors with pprint():")
        pprint(sorted(self._flake8_errors_as_string), width=150)
        print("\nAll errors with pure print():")
        for error in sorted(self._flake8_errors_as_string):
            print()
            print(f"<<<{error}>>>")
        print("\nProject root:", self.root_dir)
        raise AssertionError(assertion_message or expected_error)

    def _assert_error_count(self, expected_error: str, expected_count: int = None) -> "ProjectMock":
        """Assert the error count is correct."""
        if expected_count is not None:
            actual = len(self._flake8_errors_as_string)
            if expected_count != actual:
                self.raise_assertion_error(expected_error, "Expected {} errors, got {}".format(expected_count, actual))
        return self

    def assert_errors_contain(self, raw_error: str, expected_count: int = None) -> "ProjectMock":
        """Assert the error is in the error set."""
        expected_error = dedent(raw_error).strip()
        if expected_error not in self._flake8_errors_as_string:
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
        for actual_error in self._flake8_errors_as_string:
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
        if not self._flake8_errors_as_string:
            return self

        self.raise_assertion_error("")
        return self

    def assert_merged_style(self, toml_string: str):
        """Assert the contents of the merged style file."""
        expected = TOMLFormat(path=self.cache_dir / MERGED_STYLE_TOML)
        actual = TOMLFormat(string=dedent(toml_string))
        compare(expected.as_data, actual.as_data)
