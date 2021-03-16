"""Enums."""
import os
from enum import Enum, IntEnum, auto

from nitpick.constants import PROJECT_NAME


class _OptionMixin:
    """Private mixin used to test the CLI options."""

    name: str

    def as_flake8_flag(self) -> str:
        """Format the name of a flag to be used on the CLI."""
        slug = self.name.lower().replace("_", "-")
        return f"--{PROJECT_NAME}-{slug}"

    def as_envvar(self) -> str:
        """Format the name of an environment variable."""
        return f"{PROJECT_NAME.upper()}_{self.name.upper()}"

    def get_environ(self) -> str:
        """Get the value of an environment variable."""
        return os.environ.get(self.as_envvar(), "")


class OptionEnum(_OptionMixin, Enum):
    """Options to be used with the CLI."""

    OFFLINE = "Offline mode: no style will be downloaded (no HTTP requests at all)"


class CachingEnum(IntEnum):
    """Caching modes for styles."""

    #: Never cache, the style file(s) are always looked-up.
    NEVER = auto()

    #: Once the style(s) are cached, they never expire.
    FOREVER = auto()

    #: The cache expires after the configured amount of time (minutes/hours/days).
    EXPIRES = auto()
