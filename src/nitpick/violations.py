"""Violation codes.

Name inspired by `flake8's violations <https://flake8.pycqa.org/en/latest/user/error-codes.html>`_.
"""
from enum import Enum

from nitpick.exceptions import NitpickError
from nitpick.plugins.data import FileData


class ViolationEnum(Enum):
    """Base enum with violation codes and messages."""

    def __init__(self, code: int, message: str = "") -> None:  # FIXME[AA]: add_to_base=False
        self.code = code
        self.message = message


class SharedViolations(ViolationEnum):
    """Shared violations used by all plugins."""

    CreateFile = (1, " was not found")
    CreateFileWithSuggestion = (1, " was not found. Create it with this content:")
    DeleteFile = (2, " should be deleted")
    MissingValues = (8, "{prefix} has missing values:")
    DifferentValues = (9, "{prefix} has different values. Use this:")


class BasicViolations(ViolationEnum):
    """Basic violations (root dir, Python files, present/absent files)."""

    MissingFile = (103, " should exist{extra}")
    FileShouldBeDeleted = (104, " should be deleted{extra}")


# TODO: the Reporter class should track a global list of codes with __new__(),
#  to be used by the `nitpick codes` CLI command
class Reporter:  # pylint: disable=too-few-public-methods
    """Error reporter."""

    def __init__(self, data: FileData, violation_base_code: int = 0) -> None:
        self.data = data
        self.violation_base_code = violation_base_code

    def make_error(self, violation: ViolationEnum, suggestion: str = "", **kwargs):
        """Make an error."""  # FIXME[AA]: make a fuss
        if kwargs:
            formatted = violation.message.format(**kwargs)
        else:
            formatted = violation.message
        base = self.violation_base_code if violation.__class__ is SharedViolations else 0
        return NitpickError(f"File {self.data.path_from_root}{formatted}", suggestion, base + violation.code)
