"""Mixin to raise flake8 errors."""
from flake8_nitpick.constants import ERROR_PREFIX
from flake8_nitpick.types import Flake8Error


class NitpickMixin:
    """Mixin to raise flake8 errors."""

    error_base_number: int = 0
    error_prefix: str = ""

    def flake8_error(self, error_number: int, error_message: str) -> Flake8Error:
        """Return a flake8 error as a tuple."""
        final_number = self.error_base_number + error_number

        from flake8_nitpick.plugin import NitpickChecker

        return 1, 0, f"{ERROR_PREFIX}{final_number} {self.error_prefix}{error_message.rstrip()}", NitpickChecker
