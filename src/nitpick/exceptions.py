"""Nitpick exceptions."""
import warnings
from dataclasses import dataclass
from typing import Any, Dict, List, Union

import click
from more_itertools import always_iterable

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

    # TODO: display filename, line and (if possible) column of the error, like flake8 does with .py files
    filename: str = ""
    # lineno: int = 1
    # col: int = 0

    def __init__(self, message: str = "", suggestion: str = "", code: int = 0) -> None:
        self.code = code
        self.message: str = message or self.message
        self.suggestion: str = suggestion
        super().__init__(self.message)

    @property
    def suggestion_nl(self) -> str:
        """Suggestion with newline."""
        return click.style("\n{}".format(self.suggestion.rstrip()), fg="green") if self.suggestion else ""

    @property
    def pretty(self) -> str:
        """Message to be used on the CLI."""
        # TODO: f"{self.filename}:{self.lineno}:{self.col + 1} "
        return f"{FLAKE8_PREFIX}{self.code:03} {self.message.rstrip()}{self.suggestion_nl}"

    @property
    def as_dataclass(self):
        """Error as a dataclass."""
        return Fuss(self.filename, self.code, self.message, self.suggestion_nl)


class QuitComplaining(Exception):
    """Quit complaining and exit the application."""

    def __init__(self, nitpick_errors: Union[NitpickError, List[NitpickError]]) -> None:  # FIXME[AA]: fuss: Fuss
        super().__init__()
        self.nitpick_errors: List[NitpickError] = list(always_iterable(nitpick_errors))


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


def pretty_exception(err: Exception, message: str = ""):
    """Return a pretty error message with the full path of the Exception."""
    return f"{message} ({err.__module__}.{err.__class__.__name__}: {str(err)})"
