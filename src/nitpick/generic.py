"""Generic functions and classes.

.. testsetup::

    from nitpick.generic import *
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

import furl

from nitpick.constants import DOT, PROJECT_NAME
from nitpick.typedefs import PathOrStr


def version_to_tuple(version: str = None) -> tuple[int, ...]:
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


if sys.platform == "win32":

    def furl_path_to_python_path(path: furl.Path) -> Path:
        """Convert a file URL to a path."""
        drive, *segments = path.segments
        return Path(f"{drive}/", *segments)

    def get_scheme(url: str) -> str | None:
        """Get the scheme of a URL, or None if there is no scheme."""
        scheme = furl.get_scheme(url)
        # Windows drive letters are not a valid scheme
        return scheme if scheme and len(scheme) > 1 else None

else:

    def furl_path_to_python_path(path: furl.Path) -> Path:
        """Convert a file URL to a path."""
        return Path("/", *path.segments)

    get_scheme = furl.get_scheme
