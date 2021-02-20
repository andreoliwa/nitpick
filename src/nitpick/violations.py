"""Violation codes.

Name inspired by `flake8's violations <https://flake8.pycqa.org/en/latest/user/error-codes.html>`_.
"""
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Optional

import click

from nitpick.constants import FLAKE8_PREFIX

if TYPE_CHECKING:
    from nitpick.plugins.data import FileData


@dataclass(frozen=True)
class Fuss:
    """Nitpick makes a fuss when configuration doesn't match.

    Fields inspired on :py:class:`SyntaxError` and :py:class:`pyflakes.messages.Message`.
    """

    fixed: bool
    filename: str
    code: int
    message: str
    suggestion: str = ""
    lineno: int = 1

    @property
    def colored_suggestion(self) -> str:
        """Suggestion with color."""
        return click.style("\n{}".format(self.suggestion.rstrip()), fg="green") if self.suggestion else ""

    @property
    def pretty(self) -> str:
        """Message to be used on the CLI."""
        return (
            f"{self.filename}:{self.lineno}: {FLAKE8_PREFIX}{self.code:03}"
            f" {self.message.rstrip()}{self.colored_suggestion}"
        )


class ViolationEnum(Enum):
    """Base enum with violation codes and messages."""

    def __init__(self, code: int, message: str = "", add_to_base=False) -> None:
        self.code = code
        self.message = message
        self.add_code = add_to_base


class StyleViolations(ViolationEnum):
    """Style violations."""

    InvalidDataToolNitpick = (1, " has an incorrect style. Invalid data in [{section}]:")
    InvalidTOML = (1, " has an incorrect style. Invalid TOML{exception}")
    InvalidConfig = (1, " has an incorrect style. Invalid config:")


class ProjectViolations(ViolationEnum):
    """Project initialization violations."""

    NoRootDir = (101, "No root dir found (is this a Python project?)")
    NoPythonFile = (102, "No Python file was found on the root dir and subdir of {root!r}")
    MissingFile = (103, " should exist{extra}")
    FileShouldBeDeleted = (104, " should be deleted{extra}")

    MinimumVersion = (
        203,
        "The style file you're using requires {project}>={expected} (you have {actual}). Please upgrade",
    )


class SharedViolations(ViolationEnum):
    """Shared violations used by all plugins."""

    CreateFile = (1, " was not found", True)
    CreateFileWithSuggestion = (1, " was not found. Create it with this content:", True)
    DeleteFile = (2, " should be deleted", True)
    MissingValues = (8, "{prefix} has missing values:", True)
    DifferentValues = (9, "{prefix} has different values. Use this:", True)


# TODO: the Reporter class should track a global list of codes with __new__(),
#  to be used by the `nitpick codes` CLI command
class Reporter:  # pylint: disable=too-few-public-methods
    """Error reporter."""

    manual: int = 0
    fixed: int = 0

    def __init__(self, data: "FileData" = None, violation_base_code: int = 0) -> None:
        self.data: Optional["FileData"] = data
        self.violation_base_code = violation_base_code

    def make_fuss(self, violation: ViolationEnum, suggestion: str = "", fixed=False, **kwargs) -> Fuss:
        """Make a fuss."""
        if kwargs:
            formatted = violation.message.format(**kwargs)
        else:
            formatted = violation.message
        base = self.violation_base_code if violation.add_code else 0
        Reporter.increment(fixed)
        return Fuss(fixed, self.data.path_from_root if self.data else "", base + violation.code, formatted, suggestion)

    @classmethod
    def reset(cls):
        """Reset the counters."""
        cls.manual = cls.fixed = 0

    @classmethod
    def increment(cls, fixed=False):
        """Increment the fixed ou manual count."""
        if fixed:
            cls.fixed += 1
        else:
            cls.manual += 1

    @classmethod
    def get_counts(cls) -> str:
        """String representation with error counts and emojis."""
        parts = []
        if cls.fixed:
            parts.append(f"✅ {cls.fixed} fixed")
        if cls.manual:
            parts.append(f"❌ {cls.manual} to change manually")
        if not parts:
            return "🎖 No violations found."
        return f"Violations: {', '.join(parts)}."
