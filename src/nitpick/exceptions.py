"""Nitpick exceptions."""
from pathlib import Path


class NitpickError(Exception):
    """A Nitpick error  raise flake8 errors."""

    error_base_number = 0  # type: int
    error_prefix = ""  # type: str

    number = 0  # type: int
    message = ""  # type: str
    suggestion = None  # type: str
    add_to_base_number = True

    def __init__(self, *args: object) -> None:
        if not args:
            super().__init__(self.message)
        else:
            super().__init__(*args)


class PluginError(NitpickError):
    """Plugin error."""

    error_base_number = 100


class NoRootDir(PluginError):
    """No root dir found."""

    number = 1
    message = "No root dir found (is this a Python project?)"


class NoPythonFile(PluginError):
    """No Python file was found."""

    number = 2
    message = "No Python file was found on the root dir and subdir of {!r}"

    def __init__(self, root_dir: Path, *args: object) -> None:
        self.message = self.message.format(str(root_dir))
        super().__init__(self.message, *args)


class StyleError(NitpickError):
    """An error in a style file."""

    number = 1
    add_to_base_number = False

    def __init__(self, style_file_name: str, *args: object) -> None:
        self.style_file_name = style_file_name
        super().__init__(*args)
