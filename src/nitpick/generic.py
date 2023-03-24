"""Generic functions and classes.

.. testsetup::

    from nitpick.generic import *
"""
from __future__ import annotations

import sys
from pathlib import Path, PosixPath, WindowsPath
from typing import Iterable

from furl import furl

from nitpick.constants import DOT, PROJECT_NAME
from nitpick.typedefs import PathOrStr


def version_to_tuple(version: str | None = None) -> tuple[int, ...]:
    """Transform a version number into a tuple of integers, for comparison.

    >>> version_to_tuple("")
    ()
    >>> version_to_tuple("  ")
    ()
    >>> version_to_tuple(None)
    ()
    >>> version_to_tuple("1.0.1")
    (1, 0, 1)
    >>> version_to_tuple(" 0.2 ")
    (0, 2)
    >>> version_to_tuple(" 2 ")
    (2,)

    :param version: String with the version number. It must be integers split by dots.
    :return: Tuple with the version number.
    """
    if not version:
        return ()
    clean_version = version.strip()
    if not clean_version:
        return ()
    return tuple(int(part) for part in clean_version.split(DOT))


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
