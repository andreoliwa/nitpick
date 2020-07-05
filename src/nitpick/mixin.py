"""Mixin to raise flake8 errors."""
from nitpick.formats import Comparison
from nitpick.typedefs import Flake8Error


class NitpickMixin:
    """Mixin to raise flake8 errors."""

    error_base_number = 0  # type: int
    error_prefix = ""  # type: str

    # TODO: remove this after all errors are converted to Nitpick.as_flake8_warning()
    def flake8_error(self, number: int, message: str, suggestion: str = None, add_to_base_number=True) -> Flake8Error:
        """Return a flake8 error as a tuple."""
        # pylint: disable=import-outside-toplevel
        from nitpick.app import NitpickApp
        from nitpick.exceptions import NitpickError

        error = NitpickError()
        error.error_base_number = self.error_base_number
        error.error_prefix = self.error_prefix
        error.number = number
        error.message = message
        if suggestion:
            error.suggestion = suggestion
        error.add_to_base_number = add_to_base_number
        return NitpickApp.as_flake8_warning(error)

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
