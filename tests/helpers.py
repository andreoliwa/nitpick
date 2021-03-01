"""Test helpers."""
import os
import sys
from pathlib import Path
from pprint import pprint
from textwrap import dedent
from typing import Dict, Iterable, List, Optional, Set

import pytest
from click.testing import CliRunner
from more_itertools.more import always_iterable
from testfixtures import compare

from nitpick.cli import nitpick_cli
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
from nitpick.typedefs import Flake8Error, PathOrStr, StrOrList
from nitpick.violations import Fuss, Reporter

FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"
STYLES_DIR: Path = Path(__file__).parent.parent / "styles"

# Non-breaking space
NBSP = "\xc2\xa0"

# TODO: fix Windows tests
XFAIL_ON_WINDOWS = pytest.mark.xfail(condition=sys.platform == "win32", reason="Different path separator on Windows")


def assert_conditions(*args):
    """Assert all conditions are True."""
    for arg in args:
        if not arg:
            raise AssertionError()


class ProjectMock:
    """A mocked Python project to help on tests."""

    # TODO: use Python 3.6 type annotations

    def __init__(self, tmp_path: Path, **kwargs) -> None:
        """Create the root dir and make it the current dir (needed by NitpickChecker)."""
        self._actual_violations: Set[Fuss] = set()
        self._flake8_errors: List[Flake8Error] = []
        self._flake8_errors_as_string: Set[str] = set()

        self.root_dir: Path = tmp_path
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
        full_source_path = Path(target_dir or FIXTURES_DIR) / (target_file or link_name)
        if not full_source_path.exists():
            raise RuntimeError(f"Source file does not exist: {full_source_path}")
        path.symlink_to(full_source_path)
        if path.suffix == ".py":
            self.files_to_lint.append(path)
        return self

    def _simulate_run(self, *partial_names: str, offline=False, api=True, flake8=True, apply=False) -> "ProjectMock":
        """Simulate a manual flake8 run and using the API.

        - Clear the singleton cache.
        - Recreate the global app.
        - Change the working dir to the mocked project root.
        - Lint one of the project files. If no index is provided, use the default file that's always created.
        """
        Nitpick.singleton.cache_clear()
        os.chdir(str(self.root_dir))
        nit = Nitpick.singleton().init(offline=offline)

        if api:
            self._actual_violations = set(nit.run(*partial_names, apply=apply))

        if flake8:
            npc = NitpickFlake8Extension(filename=str(self.files_to_lint[0]))
            self._flake8_errors = list(npc.run())
            self._flake8_errors_as_string = set()
            for line, col, message, class_ in self._flake8_errors:
                if not (
                    line == 0 and col == 0 and message.startswith(FLAKE8_PREFIX) and class_ is NitpickFlake8Extension
                ):
                    raise AssertionError()
                self._flake8_errors_as_string.add(message)

        return self

    def flake8(self, offline=False):
        """Test only the flake8 plugin, no API."""
        return self._simulate_run(offline=offline, api=False)

    def api_check(self, *partial_names: str):
        """Test only the API in check mode, no flake8 plugin."""
        return self._simulate_run(*partial_names, flake8=False, apply=False)

    def api_apply(self, *partial_names: str):
        """Test only the API in apply mode, no flake8 plugin."""
        return self._simulate_run(*partial_names, flake8=False, apply=True)

    def api_check_then_apply(
        self, *expected_violations_when_applying: Fuss, partial_names: Optional[Iterable[str]] = None
    ) -> "ProjectMock":
        """Assert that check mode does not change files, and that apply mode changes them.

        Perform a series of calls and assertions:
        1. Call the API in check mode, assert violations, assert files contents were not modified.
        2. Call the API in apply mode and assert violations again.

        :param expected_violations_when_applying: Expected violations when "apply mode" is on.
        :param partial_names: Names of the files to enforce configs for.
        :return: ``self`` for method chaining (fluent interface)
        """
        partial_names = partial_names or []
        expected_filenames = set()
        expected_violations_when_checking = []
        for orig in expected_violations_when_applying:
            expected_filenames.add(orig.filename)
            expected_violations_when_checking.append(
                Fuss(False, orig.filename, orig.code, orig.message, orig.suggestion)
            )

        contents_before_check = self.read_multiple_files(expected_filenames)
        self.api_check(*partial_names).assert_violations(*expected_violations_when_checking)
        contents_after_check = self.read_multiple_files(expected_filenames)
        compare(expected=contents_before_check, actual=contents_after_check)

        return self.api_apply(*partial_names).assert_violations(*expected_violations_when_applying)

    def read_file(self, filename: PathOrStr) -> Optional[str]:
        """Read file contents.

        :param filename: Filename from project root.
        :return: File contents, or ``one`` when the file doesn't exist.
        """
        path = self.root_dir / filename
        if not filename or not path.exists():
            return None
        return path.read_text().strip()

    def read_multiple_files(self, filenames: Iterable[PathOrStr]) -> Dict[PathOrStr, Optional[str]]:
        """Read multiple files and return a hash with filename (key) and contents (value)."""
        return {filename: self.read_file(filename) for filename in filenames}

    def save_file(self, filename: PathOrStr, file_contents: str, lint: bool = None) -> "ProjectMock":
        """Save a file in the root dir with the desired contents and a new line at the end.

        Create the parent dirs if the file name contains a slash.

        :param filename: If it starts with a slash, then it's already a root.
            If it doesn't, then we add the root dir before the partial name.
        :param file_contents: Contents to save in the file.
        :param lint: Should we lint the file or not? Python (.py) files are always linted.
        """
        if str(filename).startswith("/"):
            path: Path = Path(filename)
        else:
            path = self.root_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        if lint or path.suffix == ".py":
            self.files_to_lint.append(path)
        clean = dedent(file_contents).strip()
        path.write_text(f"{clean}\n")
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
            style_path = Path(STYLES_DIR) / self.ensure_toml_extension(filename)
            self.named_style(filename, style_path.read_text())
        return self

    def named_style(self, filename: PathOrStr, file_contents: str) -> "ProjectMock":
        """Save a style file with a name. Add the .toml extension if needed."""
        return self.save_file(self.ensure_toml_extension(filename), file_contents)

    @staticmethod
    def ensure_toml_extension(filename: PathOrStr) -> PathOrStr:
        """Ensure a file name has the .toml extension."""
        return filename if str(filename).endswith(".toml") else f"{filename}.toml"

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
                self.raise_assertion_error(expected_error, f"Expected {expected_count} errors, got {actual}")
        return self

    def assert_errors_contain(self, raw_error: str, expected_count: int = None) -> "ProjectMock":
        """Assert the error is in the error set."""
        expected_error = dedent(raw_error).strip()
        if expected_error not in self._flake8_errors_as_string:
            self.raise_assertion_error(expected_error)
        self._assert_error_count(expected_error, expected_count)
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

    def assert_merged_style(self, toml_string: str) -> "ProjectMock":
        """Assert the contents of the merged style file."""
        expected = TOMLFormat(path=self.cache_dir / MERGED_STYLE_TOML)
        actual = TOMLFormat(string=dedent(toml_string))
        compare(expected.as_data, actual.as_data)
        return self

    def assert_violations(self, *expected_violations: Fuss) -> "ProjectMock":
        """Assert the exact set of violations."""
        manual: int = 0
        fixed: int = 0

        stripped: Set[Fuss] = set()
        for orig in expected_violations:
            if orig.fixed:
                fixed += 1
            else:
                manual += 1

            # Keep non-breaking space needed by some tests (e.g. YAML)
            clean_suggestion = dedent(orig.suggestion).strip().replace(NBSP, " ")
            stripped.add(Fuss(orig.fixed, orig.filename, orig.code, orig.message, clean_suggestion))
        dict_difference = compare(
            expected=[obj.__dict__ for obj in stripped],
            actual=[obj.__dict__ for obj in self._actual_violations],
            raises=False,
        )
        compare(
            expected=stripped,
            actual=self._actual_violations,
            suffix=f"Comparing Fuss objects as dictionaries: {dict_difference}",
        )
        compare(expected=fixed, actual=Reporter.fixed)
        compare(expected=manual, actual=Reporter.manual)
        return self

    def _simulate_cli(self, command: str, str_or_lines: StrOrList = None, *args: str):
        result = CliRunner().invoke(nitpick_cli, ["--project", str(self.root_dir), command, *args])
        actual: List[str] = result.output.splitlines()

        if isinstance(str_or_lines, str):
            expected = dedent(str_or_lines).strip().splitlines()
        else:
            expected = list(always_iterable(str_or_lines))
        return result, actual, expected

    def cli_run(self, str_or_lines: StrOrList = None, apply=False, violations=0) -> "ProjectMock":
        """Assert the expected CLI output for the chosen command."""
        cli_args = [] if apply else ["--check"]
        result, actual, expected = self._simulate_cli("run", str_or_lines, *cli_args)
        if violations:
            expected.append(f"Violations: ❌ {violations} to change manually.")
        elif str_or_lines:
            # If the number of violations was not passed but a list of errors was,
            # remove the violation count from the actual results.
            # This is useful when checking only if the error is contained in a list of errors,
            # regardless of the violation count.
            assert actual
            del actual[-1]

        compare(actual=actual, expected=expected)
        compare(actual=result.exit_code, expected=(1 if str_or_lines else 0))
        return self

    def cli_ls(self, str_or_lines: StrOrList):
        """Run the ls command and assert the output."""
        _, actual, expected = self._simulate_cli("ls", str_or_lines)
        compare(actual=actual, expected=expected)

    def assert_file_contents(self, filename: PathOrStr, file_contents: str):
        """Assert the file has the expected contents."""
        actual = self.read_file(filename)
        expected = dedent(file_contents).strip()
        compare(actual=actual, expected=expected)
