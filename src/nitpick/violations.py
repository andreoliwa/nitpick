"""Violation codes.

Name inspired by `flake8's violations <https://flake8.pycqa.org/en/latest/user/error-codes.html>`_.
"""
from enum import Enum
from typing import TYPE_CHECKING, Optional

from nitpick.exceptions import NitpickError

if TYPE_CHECKING:
    from nitpick.plugins.data import FileData


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

    def __init__(self, data: "FileData" = None, violation_base_code: int = 0) -> None:
        self.data: Optional["FileData"] = data
        self.violation_base_code = violation_base_code

    def make_error(self, violation: ViolationEnum, suggestion: str = "", **kwargs) -> NitpickError:
        """Make an error."""  # FIXME[AA]: make a fuss
        prefix = f"File {self.data.path_from_root}" if self.data else ""
        if kwargs:
            formatted = violation.message.format(**kwargs)
        else:
            formatted = violation.message
        base = self.violation_base_code if violation.add_code else 0
        return NitpickError(f"{prefix}{formatted}", suggestion, base + violation.code)
