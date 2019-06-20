"""Mixin to raise flake8 errors."""
import click

from nitpick.constants import ERROR_PREFIX
from nitpick.formats import Comparison
from nitpick.typedefs import Flake8Error


class NitpickMixin:
    """Mixin to raise flake8 errors."""

    error_base_number = 0  # type: int
    error_prefix = ""  # type: str

    def flake8_error(self, number: int, message: str, suggestion: str = None) -> Flake8Error:
        """Return a flake8 error as a tuple."""
        joined_number = self.error_base_number + number
        suggestion_with_newline = (
            click.style("\n{}".format(suggestion.rstrip()), fg="bright_green") if suggestion else ""
        )

        from nitpick.plugin import NitpickChecker

        return (
            1,
            0,
            "{}{} {}{}{}".format(
                ERROR_PREFIX, joined_number, self.error_prefix, message.rstrip(), suggestion_with_newline
            ),
            NitpickChecker,
        )

    def warn_missing_different(self, comparison: Comparison, prefix_message: str = ""):
        """Warn about missing and different keys."""
        if comparison.missing_format:
            yield self.flake8_error(
                8, "{} has missing values:".format(prefix_message), comparison.missing_format.reformatted
            )
        if comparison.diff_format:
            yield self.flake8_error(
                9, "{} has different values. Use this:".format(prefix_message), comparison.diff_format.reformatted
            )
