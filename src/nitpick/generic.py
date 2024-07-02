"""Generic functions and classes.

.. testsetup::

    from nitpick.generic import *
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path, PosixPath, WindowsPath
from typing import TYPE_CHECKING, Iterable

import click
from gitignore_parser import parse_gitignore

from nitpick.constants import DOT, GIT_CORE_EXCLUDES_FILE, GIT_DIR, GIT_IGNORE, PROJECT_NAME

if TYPE_CHECKING:
    from furl import furl

    from nitpick.typedefs import PathOrStr


def relative_to_current_dir(path_or_str: PathOrStr | None) -> str:
    """Return a relative path to the current dir or an absolute path."""
    if not path_or_str:
        return ""

    path = Path(path_or_str)
    if str(path).startswith(str(Path.cwd())):
        rv = str(path.relative_to(Path.cwd()))
        return "" if rv == DOT else rv

    return str(path.absolute())


def filter_names(iterable: Iterable, *partial_names: str) -> list[str]:
    """Filter names and keep only the desired partial names.

    Exclude the project name automatically.

    >>> file_list = ['requirements.txt', 'tox.ini', 'setup.py', 'nitpick']
    >>> filter_names(file_list)
    ['requirements.txt', 'tox.ini', 'setup.py']
    >>> filter_names(file_list, 'ini', '.py')
    ['tox.ini', 'setup.py']

    >>> mapping = {'requirements.txt': None, 'tox.ini': 1, 'setup.py': 2, 'nitpick': 3}
    >>> filter_names(mapping)
    ['requirements.txt', 'tox.ini', 'setup.py']
    >>> filter_names(file_list, 'x')
    ['requirements.txt', 'tox.ini']
    """
    rv = []
    for name in iterable:
        if name == PROJECT_NAME:
            continue

        include = bool(not partial_names)
        for partial_name in partial_names:
            if partial_name in name:
                include = True
                break

        if include:
            rv.append(name)
    return rv


def _url_to_windows_path(url: furl) -> Path:
    """Convert the segments of a file URL to a path."""
    # ref: https://docs.microsoft.com/en-us/dotnet/standard/io/file-path-formats
    # UNC file path, \\server\share\path..., with server stored as url.host
    # DOS Path, drive_letter:\path...
    share_or_drive, *segments = url.path.segments
    share_or_drive = rf"\\{url.host}\{share_or_drive}" if url.host else rf"{share_or_drive}\\"
    return WindowsPath(share_or_drive, *segments)


def _url_to_posix_path(url: furl) -> Path:
    """Convert the segments of a file URL to a path."""
    # ref: https://unix.stackexchange.com/a/1919
    # POSIX paths can start with //part/..., which some implementations
    # (such as Cygwin) can interpret differently. furl(Path("//part/...").as_uri())
    # retains the double slash (but doesn't treat it as a host), and in that case
    # `first` will always be an empty string and `segments` will *not* be empty.
    first, *segments = url.path.segments
    slash_or_double_slash = "//" if not first and segments else "/"
    return PosixPath(slash_or_double_slash, first, *segments)


url_to_python_path = _url_to_windows_path if sys.platform == "win32" else _url_to_posix_path


def glob_files(dir_: Path, file_patterns: Iterable[str]) -> set[Path]:
    """Search a directory looking for file patterns."""
    for pattern in file_patterns:
        found_files = set(dir_.glob(pattern))
        if found_files:
            return found_files
    return set()


def get_global_gitignore_path() -> Path | None:
    """Get the path to the global Git ignore file."""
    try:
        output = subprocess.check_output(  # noqa: S603
            # TODO: fix: this command might not work on Windows; maybe read ~/.gitconfig directly instead?
            ["git", "config", "--get", GIT_CORE_EXCLUDES_FILE],  # noqa: S607
            universal_newlines=True,
        ).strip()
        return Path(output) if output else None
    except subprocess.CalledProcessError:
        click.secho(
            f"The '{GIT_CORE_EXCLUDES_FILE}' configuration is not set or does not exist.", err=True, fg="yellow"
        )
    except FileNotFoundError:
        click.secho("Git command not found. Please make sure Git is installed and on the PATH.", err=True, fg="red")
    return None


def glob_non_ignored_files(root_dir: Path, pattern: str = "**/*") -> Iterable[Path]:
    """Glob all files in the root dir that are not ignored by Git."""

    git_dir = root_dir / GIT_DIR
    is_locally_ignored = None
    is_globally_ignored = None
    if git_dir.is_dir():
        global_gitignore = get_global_gitignore_path()
        if global_gitignore and global_gitignore.is_file():
            is_globally_ignored = parse_gitignore(global_gitignore)
        local_gitignore_path = root_dir / GIT_IGNORE
        if local_gitignore_path.is_file():
            is_locally_ignored = parse_gitignore(local_gitignore_path)

    for project_file in root_dir.glob(pattern):
        if (
            not project_file.is_file()
            or (is_globally_ignored and is_globally_ignored(project_file))
            or (is_locally_ignored and is_locally_ignored(project_file))
        ):
            continue
        yield project_file
