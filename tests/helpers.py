"""Test helpers."""
from __future__ import annotations

import os
from pathlib import Path
from pprint import pprint
from textwrap import dedent
from typing import Any, Iterable

import tomlkit
from click.testing import CliRunner
from more_itertools.more import always_iterable, windowed
from responses import RequestsMock
from testfixtures import compare

from nitpick.blender import TomlDoc
from nitpick.cli import nitpick_cli
from nitpick.constants import (
    CACHE_DIR_NAME,
    FLAKE8_PREFIX,
    MERGED_STYLE_TOML,
    NITPICK_STYLE_TOML,
    PRE_COMMIT_CONFIG_YAML,
    PROJECT_NAME,
    PYPROJECT_TOML,
    SETUP_CFG,
)
from nitpick.core import Nitpick
from nitpick.flake8 import NitpickFlake8Extension
from nitpick.typedefs import Flake8Error, PathOrStr, StrOrList
from nitpick.violations import Fuss, Reporter

STYLES_DIR: Path = Path(__file__).parent.parent / "src" / "nitpick" / "resources"

# Non-breaking space
NBSP = "\xc2\xa0"

SUGGESTION_BEGIN = "\x1b[32m"
SUGGESTION_END = "\x1b[0m"


def assert_conditions(*args):
    """Assert all conditions are True."""
    for arg in args:
        if not arg:
            raise AssertionError()


def from_path_or_str(file_contents: PathOrStr):
    """Read file contents from a Path or string."""
    if file_contents is None:
        raise RuntimeError("No path and no file contents.")

    if isinstance(file_contents, Path):
        return file_contents.read_text()

    return file_contents


def tomlstring(value: Any) -> str:
    """Create a fully-quoted TOML string from a path.

    This ensures proper quoting of Windows paths and other values with backslashes.

    """
    return tomlkit.string(str(value)).as_string()


class ProjectMock:
    """A mocked Python project to help on tests."""

    def __init__(self, tmp_path: Path, **kwargs) -> None:
        """Create the root dir and make it the current dir (needed by NitpickChecker)."""
        self._actual_violations: set[Fuss] = set()
        self._flake8_errors: list[Flake8Error] = []
        self._flake8_errors_as_string: set[str] = set()

        self.nitpick_instance: Nitpick | None = None
        self.root_dir: Path = tmp_path
        self.cache_dir = self.root_dir / CACHE_DIR_NAME / PROJECT_NAME
        self._mocked_response: RequestsMock | None = None
        self._remote_url: str | None = None
        self.files_to_lint: list[Path] = []

        if kwargs.get("setup_py", True):
            self.save_file("setup.py", "x = 1")

    def create_symlink(self, link_name: str, target_dir: Path, target_file: str | None = None) -> ProjectMock:
        """Create a symlink to a target file.

        :param link_name: Link file name.
        :param target_dir: Target directory (default: fixture directory).
        :param target_file: Target file name (default: source file name).
        """
        path: Path = self.root_dir / link_name
        full_source_path = Path(target_dir) / (target_file or link_name)
        if not full_source_path.exists():
            raise RuntimeError(f"Source file does not exist: {full_source_path}")
        path.symlink_to(full_source_path)
        if path.suffix == ".py":
            self.files_to_lint.append(path)
        return self

    def _simulate_run(self, *partial_names: str, offline=False, api=True, flake8=True, autofix=False) -> ProjectMock:
        """Simulate a manual flake8 run and using the API.

        - Clear the singleton cache.
        - Recreate the global app.
        - Change the working dir to the mocked project root.
        - Lint one of the project files. If no index is provided, use the default file that's always created.
        """
        Nitpick.singleton.cache_clear()
        os.chdir(str(self.root_dir))
        self.nitpick_instance = Nitpick.singleton().init(offline=offline)

        if api:
            self._actual_violations = set(self.nitpick_instance.run(*partial_names, autofix=autofix))

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

    def api_check(self, *partial_names: str, offline=False):
        """Test only the API in check mode, no flake8 plugin."""
        return self._simulate_run(*partial_names, offline=offline, api=True, flake8=False, autofix=False)

    def api_fix(self, *partial_names: str):
        """Test only the API in autofix mode, no flake8 plugin."""
        return self._simulate_run(*partial_names, api=True, flake8=False, autofix=True)

    def api_check_then_fix(
        self, *expected_violations_when_fixing: Fuss, partial_names: Iterable[str] | None = None
    ) -> ProjectMock:
        """Assert that check mode does not change files, and that autofix mode changes them.

        Perform a series of calls and assertions:
        1. Call the API in check mode, assert violations, assert files contents were not modified.
        2. Call the API in autofix mode and assert violations again.

        :param expected_violations_when_fixing: Expected violations when "autofix mode" is on.
        :param partial_names: Names of the files to enforce configs for.
        :return: ``self`` for method chaining (fluent interface)
        """
        partial_names = partial_names or []
        expected_filenames = set()
        expected_violations_when_checking = []
        for orig in expected_violations_when_fixing:
            expected_filenames.add(orig.filename)
            expected_violations_when_checking.append(
                Fuss(False, orig.filename, orig.code, orig.message, orig.suggestion)
            )

        contents_before_check = self.read_multiple_files(expected_filenames)
        self.api_check(*partial_names).assert_violations(*expected_violations_when_checking, disclaimer="Check")
        contents_after_check = self.read_multiple_files(expected_filenames)
        compare(expected=contents_before_check, actual=contents_after_check)

        return self.api_fix(*partial_names).assert_violations(*expected_violations_when_fixing, disclaimer="Fix")

    def path_for(self, filename: PathOrStr) -> str:
        """Return the full path for a file, based on the root dir."""
        return str(self.root_dir / filename)

    def read_file(self, filename: PathOrStr) -> str | None:
        """Read file contents.

        :param filename: Filename from project root.
        :return: File contents, or ``one`` when the file doesn't exist.
        """
        path = self.root_dir / filename
        if not filename or not path.exists():
            return None
        return path.read_text()

    def read_multiple_files(self, filenames: Iterable[PathOrStr]) -> dict[PathOrStr, str | None]:
        """Read multiple files and return a hash with filename (key) and contents (value)."""
        return {filename: self.read_file(filename) for filename in filenames}

    def save_file(self, filename: PathOrStr, file_contents: PathOrStr, lint: bool | None = None) -> ProjectMock:
        """Save a file in the root dir with the desired contents and a new line at the end.

        Create the parent dirs if the file name contains a slash.

        :param filename: If an absolute path, then it's already a root.
            If it isn't, then we add the root dir before the partial name.
        :param file_contents: Contents to save in the file.
        :param lint: Should we lint the file or not? Python (.py) files are always linted.
        """
        path: Path = Path(filename)
        if not path.is_absolute():
            path = self.root_dir / path
        path.parent.mkdir(parents=True, exist_ok=True)
        if lint or path.suffix == ".py":
            self.files_to_lint.append(path)
        clean = dedent(from_path_or_str(file_contents)).strip()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{clean}\n")
        return self

    def touch_file(self, filename: PathOrStr) -> ProjectMock:
        """Save an empty file (like the ``touch`` command)."""
        return self.save_file(filename, "")

    def style(self, file_contents: PathOrStr) -> ProjectMock:
        """Save the default style file."""
        return self.save_file(NITPICK_STYLE_TOML, from_path_or_str(file_contents))

    # TODO: test: remove this function, don't test real styles anymore to avoid breaking tests on Renovate updates
    def load_styles(self, *args: PathOrStr) -> ProjectMock:
        """Load style files from the 'styles' dir, to be used on tests.

        If a style file is modified (file name or contents), tests might break.
        This is a good way to test the style files indirectly.
        """
        for filename in args:
            style_path = Path(STYLES_DIR) / self.ensure_toml_extension(filename)
            self.named_style(filename, style_path.read_text())
        return self

    def named_style(self, filename: PathOrStr, file_contents: PathOrStr) -> ProjectMock:
        """Save a style file with a name. Add the .toml extension if needed."""
        return self.save_file(self.ensure_toml_extension(filename), from_path_or_str(file_contents))

    @staticmethod
    def ensure_toml_extension(filename: PathOrStr) -> PathOrStr:
        """Ensure a file name has the .toml extension."""
        return filename if str(filename).endswith(".toml") else f"{filename}.toml"

    def setup_cfg(self, file_contents: PathOrStr) -> ProjectMock:
        """Save setup.cfg."""
        return self.save_file(SETUP_CFG, from_path_or_str(file_contents))

    def pyproject_toml(self, file_contents: PathOrStr) -> ProjectMock:
        """Save pyproject.toml."""
        return self.save_file(PYPROJECT_TOML, from_path_or_str(file_contents))

    def pre_commit(self, file_contents: PathOrStr) -> ProjectMock:
        """Save .pre-commit-config.yaml."""
        return self.save_file(PRE_COMMIT_CONFIG_YAML, from_path_or_str(file_contents))

    def raise_assertion_error(self, expected_error: str, assertion_message: str | None = None):
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

    def _assert_error_count(self, expected_error: str, expected_count: int | None = None) -> ProjectMock:
        """Assert the error count is correct."""
        if expected_count is not None:
            actual = len(self._flake8_errors_as_string)
            if expected_count != actual:
                self.raise_assertion_error(expected_error, f"Expected {expected_count} errors, got {actual}")
        return self

    def assert_errors_contain(self, raw_error: str, expected_count: int | None = None) -> ProjectMock:
        """Assert the error is in the error set."""
        expected_error = dedent(raw_error).strip()
        if expected_error not in self._flake8_errors_as_string:
            self.raise_assertion_error(expected_error)
        self._assert_error_count(expected_error, expected_count)
        return self

    def assert_single_error(self, raw_error: str) -> ProjectMock:
        """Assert there is only one error."""
        return self.assert_errors_contain(raw_error, 1)

    def assert_no_errors(self) -> ProjectMock:
        """Assert that there are no errors."""
        if not self._flake8_errors_as_string:
            return self

        self.raise_assertion_error("")
        return self

    def assert_merged_style(self, toml_string: str) -> ProjectMock:
        """Assert the contents of the merged style file."""
        expected = TomlDoc(path=self.cache_dir / MERGED_STYLE_TOML)
        actual = TomlDoc(string=dedent(toml_string))
        compare(expected.as_object, actual.as_object)
        return self

    def assert_violations(self, *expected_violations: Fuss, disclaimer="") -> ProjectMock:
        """Assert the exact set of violations."""
        manual: int = 0
        fixed: int = 0

        stripped: set[Fuss] = set()
        for orig in expected_violations:
            if orig.fixed:
                fixed += 1
            else:
                manual += 1

            # Keep non-breaking space needed by some tests (e.g. YAML)
            clean_suggestion = dedent(orig.suggestion).strip().replace(NBSP, " ")
            stripped.add(Fuss(orig.fixed, orig.filename, orig.code, orig.message, clean_suggestion))
        dict_difference = compare(
            expected=[obj.__dict__ for obj in sorted(stripped)],
            actual=[obj.__dict__ for obj in sorted(self._actual_violations)],
            raises=False,
        )
        prefix = f"[{disclaimer}] " if disclaimer else ""
        compare(
            expected=stripped,
            actual=self._actual_violations,
            suffix=f"{prefix}Comparing Fuss objects as dictionaries: {dict_difference}",
        )
        compare(expected=fixed, actual=Reporter.fixed)
        compare(expected=manual, actual=Reporter.manual)
        return self

    def _simulate_cli(
        self, command: str, expected_str_or_lines: StrOrList | None = None, *args: str, exit_code: int | None = None
    ):
        """Simulate the CLI by invoking a click command.

        1. If the command raised an exception that was not a common "system exit",
            this method will re-raise it, so the test can be fixed.
        """
        result = CliRunner().invoke(nitpick_cli, ["--project", str(self.root_dir), command, *args])

        # 1.
        if result.exception and not isinstance(result.exception, SystemExit):
            raise result.exception

        actual: list[str] = result.output.splitlines()

        if isinstance(expected_str_or_lines, str):
            expected = dedent(expected_str_or_lines).strip().splitlines()
        else:
            expected = list(always_iterable(expected_str_or_lines))

        compare(actual=result.exit_code, expected=exit_code or 0)

        return result, actual, expected

    def cli_run(
        self,
        expected_str_or_lines: StrOrList | None = None,
        autofix=False,
        violations=0,
        exception_class=None,
        exit_code: int | None = None,
    ) -> ProjectMock:
        """Assert the expected CLI output for the chosen command."""
        if exit_code is None:
            exit_code = 1 if expected_str_or_lines else 0
        result, actual, expected = self._simulate_cli(
            "fix" if autofix else "check", expected_str_or_lines, exit_code=exit_code
        )
        if exception_class:
            assert isinstance(result.exception, exception_class)
            return self

        if violations:
            expected.append(f"Violations: ❌ {violations} to change manually.")
        elif expected_str_or_lines:
            # If the number of violations was not passed but a list of errors was,
            # remove the violation count from the actual results.
            # This is useful when checking only if the error is contained in a list of errors,
            # regardless of the violation count.
            assert actual
            if actual[-1].startswith("Violations"):
                del actual[-1]

        if not violations and not expected_str_or_lines:
            # Remove the "no violations" message
            if actual[-1].startswith("No violations"):
                del actual[-1]

        compare(actual=actual, expected=expected)
        return self

    def cli_ls(self, str_or_lines: StrOrList, *, exit_code: int | None = None) -> ProjectMock:
        """Run the ls command and assert the output."""
        result, actual, expected = self._simulate_cli("ls", str_or_lines, exit_code=exit_code)
        compare(actual=actual, expected=expected, prefix=f"Result: {result}")
        return self

    def cli_init(self, str_or_lines: StrOrList, *args, exit_code: int | None = None) -> ProjectMock:
        """Run the init command and assert the output."""
        result, actual, expected = self._simulate_cli("init", str_or_lines, *args, exit_code=exit_code)
        compare(actual=actual, expected=expected, prefix=f"Result: {result}")
        return self

    def assert_file_contents(self, *name_contents: PathOrStr | str | None) -> ProjectMock:
        """Assert the file has the expected contents. Use `None` to indicate that the file doesn't exist."""
        assert len(name_contents) % 2 == 0, "Supply pairs of arguments: filename (PathOrStr) and file contents (str)"
        for filename, file_contents in windowed(name_contents, 2, step=2):
            actual = self.read_file(filename)
            expected = None if file_contents is None else dedent(from_path_or_str(file_contents)).lstrip()
            compare(actual=actual, expected=expected, prefix=f"Filename: {filename}")
        return self

    def remote(self, mocked_response: RequestsMock, remote_url: str) -> ProjectMock:
        """Set the mocked response and the remote URL."""
        self._mocked_response = mocked_response
        self._remote_url = remote_url
        return self

    def assert_call_count(self, expected_count: int) -> ProjectMock:
        """Assert the expected request count on the mocked response object."""
        assert self._mocked_response and self._mocked_response.assert_call_count(self._remote_url, expected_count)
        return self
