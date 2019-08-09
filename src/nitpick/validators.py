"""Marshmallow validators."""
from marshmallow.validate import Length


class TrimmedLength(Length):  # pylint: disable=too-few-public-methods
    """Trim the string before validating the length."""

    def __call__(self, value):
        """Validate the trimmed string."""
        return super().__call__(value.strip())
