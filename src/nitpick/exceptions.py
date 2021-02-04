"""Nitpick exceptions."""
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import click

from nitpick.constants import FLAKE8_PREFIX, PROJECT_NAME


@dataclass
class Fuss:
    """Nitpick makes a fuss when configuration doesn't match.

    Fields inspired on :py:class:`SyntaxError` and :py:class:`pyflakes.messages.Message`.
    """

    filename: str
    code: int
    message: str
    suggestion: str = ""


class NitpickError(Exception):  # TODO: use a dataclass instead of inheriting from Exception?
    """The base class for Nitpick exceptions."""

    violation_base_code: int = 0
    error_prefix: str = ""
    message: str = ""
    number: int = 0
    add_to_base_number: bool = True

    # TODO: display filename, line and (if possible) column of the error, like flake8 does with .py files
    filename: str = ""
    # lineno: int = 1
    # col: int = 0

    def __init__(self, message: str = "", suggestion: str = "", number: int = 0, add_to_base_number=True) -> None:
        self.message: str = message or self.message
        self.suggestion: str = suggestion
        if number:
            self.number = number
        self.add_to_base_number = add_to_base_number

        super().__init__(self.message)

    @property
    def suggestion_nl(self) -> str:
        """Suggestion with newline."""
        return click.style("\n{}".format(self.suggestion.rstrip()), fg="green") if self.suggestion else ""

    @property
    def error_code(self) -> int:
        """Joined number, adding the base number with this class' number."""
        return self.violation_base_code + self.number if self.add_to_base_number else self.number

    @property
    def pretty(self) -> str:
        """Message to be used on the CLI."""
        # TODO: f"{self.filename}:{self.lineno}:{self.col + 1} "
        return f"{FLAKE8_PREFIX}{self.error_code:03} {self.error_prefix}{self.message.rstrip()}{self.suggestion_nl}"

    @property
    def as_dataclass(self):
        """Error as a dataclass."""
        return Fuss(self.filename, self.error_code, self.message, self.suggestion_nl)


class InitError(NitpickError):
    """Init errors."""

    violation_base_code = 100


class NoRootDirError(InitError):
    """No root dir found."""

    number = 1
    message = "No root dir found (is this a Python project?)"


class NoPythonFileError(InitError):
    """No Python file was found."""

    number = 2
    message = "No Python file was found on the root dir and subdir of {!r}"

    def __init__(self, root_dir: Path, **kwargs) -> None:
        self.message = self.message.format(str(root_dir))
        super().__init__(self.message, **kwargs)


class ConfigError(NitpickError):
    """Config error."""

    violation_base_code = 200


class MinimumVersionError(ConfigError):
    """Warn about minimum Nitpick version."""

    number = 3
    message = "The style file you're using requires {project}>={expected} (you have {actual}). Please upgrade"

    def __init__(self, expected: str, actual: str) -> None:
        super().__init__(self.message.format(project=PROJECT_NAME, expected=expected, actual=actual))


class StyleError(NitpickError):
    """An error in a style file."""

    number = 1
    add_to_base_number = False

    def __init__(self, style_filename: str, message: str = "", suggestion: str = "", **kwargs) -> None:
        message = f"File {style_filename} has an incorrect style. {message}"
        super().__init__(message, suggestion, **kwargs)


class Deprecation:
    """All deprecation messages in a single class.

    When it's time to break compatibility, remove a method/warning below,
    and older config files will trigger validation errors on Nitpick.
    """

    @staticmethod
    def pre_commit_without_dash(path_from_root: str) -> bool:
        """The pre-commit config should start with a dot on the config file."""
        from nitpick.plugins.pre_commit import PreCommitPlugin  # pylint: disable=import-outside-toplevel

        if path_from_root == PreCommitPlugin.filename[1:]:
            warnings.warn(
                'The section name for dotfiles should start with a dot: [".{}"]'.format(path_from_root),
                DeprecationWarning,
            )
            return True

        return False

    @staticmethod
    def jsonfile_section(style_errors: Dict[str, Any], is_merged_style: bool) -> bool:
        """The [nitpick.JSONFile] is not needed anymore; JSON files are now detected by the extension."""
        has_nitpick_jsonfile_section = style_errors.get(PROJECT_NAME, {}).pop("JSONFile", None)
        if has_nitpick_jsonfile_section:
            if not style_errors[PROJECT_NAME]:
                style_errors.pop(PROJECT_NAME)
            if not is_merged_style:
                warnings.warn(
                    "The [nitpick.JSONFile] section is not needed anymore; just declare your JSON files directly",
                    DeprecationWarning,
                )
                return True
        return False


def pretty_exception(err: Exception, message: str):
    """Return a pretty error message with the full path of the Exception."""
    return f"{message} ({err.__module__}.{err.__class__.__name__}: {str(err)})"
