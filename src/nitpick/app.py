"""The Nitpick application."""


class Nitpick:
    """The Nitpick application."""

    _current_app = None  # type: Nitpick

    def __init__(self) -> None:
        from nitpick.config import Config

        self.config = Config()

    @classmethod
    def create_app(cls) -> "Nitpick":
        """Create a single application."""
        cls._current_app = cls()
        return cls._current_app

    @classmethod
    def current_app(cls):
        """Get the current app from the stack."""
        return cls._current_app

    @classmethod
    def reset_current_app(cls):
        """Reset the current app (it's a singleton). Useful on automated tests, to simulate ``flake8`` execution."""
        cls._current_app = cls()
        return cls._current_app
