"""Mixin to raise flake8 errors."""
from typing import Optional, Type

from nitpick.exceptions import NitpickError
from nitpick.formats import Comparison
from nitpick.typedefs import Flake8Error


class NitpickMixin:
    """Mixin to raise flake8 errors."""

    error_base_number = 0  # type: int
    error_prefix = ""  # type: str
    error_class: Optional[Type[NitpickError]] = None

    # TODO: remove this after all errors are converted to Nitpick.as_flake8_warning()
    def flake8_error(self, number: int, message: str, suggestion: str = "", add_to_base_number=True) -> Flake8Error:
        """Return a flake8 error as a tuple."""
        err = NitpickError(message, suggestion, number, add_to_base_number)
        err.error_base_number = self.error_base_number
        err.error_prefix = self.error_prefix
        return err.as_flake8_warning()

    def warn_missing_different(self, comparison: Comparison, prefix_message: str = ""):
        """Warn about missing and different keys."""
        # pylint: disable=not-callable
        if comparison.missing_format:
            message = f"{prefix_message} has missing values:"
            if self.error_class:
                yield self.error_class(message, comparison.missing_format.reformatted, 8).as_flake8_warning()
            else:
                yield self.flake8_error(8, message, comparison.missing_format.reformatted)
        if comparison.diff_format:
            message = f"{prefix_message} has different values. Use this:"
            if self.error_class:
                yield self.error_class(message, comparison.diff_format.reformatted, 9).as_flake8_warning()
            else:
                yield self.flake8_error(9, message, comparison.diff_format.reformatted)
