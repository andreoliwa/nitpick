"""Mixin to raise flake8 errors."""
from nitpick.constants import ERROR_PREFIX
from nitpick.formats import Comparison
from nitpick.typedefs import Flake8Error


class NitpickMixin:
    """Mixin to raise flake8 errors."""

    error_base_number = 0  # type: int
    error_prefix = ""  # type: str

    def flake8_error(self, error_number: int, error_message: str) -> Flake8Error:
        """Return a flake8 error as a tuple."""
        final_number = self.error_base_number + error_number

        from nitpick.plugin import NitpickChecker

        return (
            1,
            0,
            "{}{} {}{}".format(ERROR_PREFIX, final_number, self.error_prefix, error_message.rstrip()),
            NitpickChecker,
        )

    def warn_missing_different(self, comparison: Comparison, prefix_message: str = ""):
        """Warn about missing and different keys."""
        if comparison.missing_format:
            yield self.flake8_error(
                8, "{} has missing values:\n{}".format(prefix_message, comparison.missing_format.reformatted)
            )
        if comparison.diff_format:
            yield self.flake8_error(
                9, "{} has different values. Use this:\n{}".format(prefix_message, comparison.diff_format.reformatted)
            )
