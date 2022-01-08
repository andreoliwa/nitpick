"""Generic functions and classes.

.. testsetup::

    from nitpick.generic import *
"""
import re
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from nitpick.constants import DOUBLE_QUOTE, PROJECT_NAME, SEPARATOR_QUOTED_SPLIT, SINGLE_QUOTE
from nitpick.typedefs import PathOrStr

URL_RE = re.compile(r"[a-z]+://[\$\w]\w*")


def get_subclasses(cls):
    """Recursively get subclasses of a parent class."""
    subclasses = []
    for subclass in cls.__subclasses__():
        subclasses.append(subclass)
        subclasses += get_subclasses(subclass)
    return subclasses


def quoted_split(string_: str, separator=".") -> List[str]:
    """Split a string by a separator, but considering quoted parts (single or double quotes).

    >>> quoted_split("my.key.without.quotes")
    ['my', 'key', 'without', 'quotes']
    >>> quoted_split('"double.quoted.string"')
    ['double.quoted.string']
    >>> quoted_split('"double.quoted.string".and.after')
    ['double.quoted.string', 'and', 'after']
    >>> quoted_split('something.before."double.quoted.string"')
    ['something', 'before', 'double.quoted.string']
    >>> quoted_split("'single.quoted.string'")
    ['single.quoted.string']
    >>> quoted_split("'single.quoted.string'.and.after")
    ['single.quoted.string', 'and', 'after']
    >>> quoted_split("something.before.'single.quoted.string'")
    ['something', 'before', 'single.quoted.string']
    """
    if DOUBLE_QUOTE not in string_ and SINGLE_QUOTE not in string_:
        return string_.split(separator)

    quoted_regex = re.compile(
        f"([{SINGLE_QUOTE}{DOUBLE_QUOTE}][^{SINGLE_QUOTE}{DOUBLE_QUOTE}]+[{SINGLE_QUOTE}{DOUBLE_QUOTE}])"
    )

    def remove_quotes(match):
        return match.group(0).strip("".join([SINGLE_QUOTE, DOUBLE_QUOTE])).replace(separator, SEPARATOR_QUOTED_SPLIT)

    return [
        part.replace(SEPARATOR_QUOTED_SPLIT, separator)
        for part in quoted_regex.sub(remove_quotes, string_).split(separator)
    ]


def version_to_tuple(version: str = None) -> Tuple[int, ...]:
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
    return tuple(int(part) for part in clean_version.split("."))


def is_url(url: str) -> bool:
    """Return True if a string is a URL.

    >>> is_url("")
    False
    >>> is_url("  ")
    False
    >>> is_url("http://example.com")
    True
    >>> is_url("github://andreoliwa/nitpick/styles/black")
    True
    >>> is_url("github://$VARNAME@andreoliwa/nitpick/styles/black")
    True
    >>> is_url("github://LitErAl@andreoliwa/nitpick/styles/black")
    True
    >>> is_url("github://notfirst$@andreoliwa/nitpick/styles/black")
    True
    """
    return bool(URL_RE.match(url))


def relative_to_current_dir(path_or_str: Optional[PathOrStr]) -> str:
    """Return a relative path to the current dir or an absolute path."""
    if not path_or_str:
        return ""

    path = Path(path_or_str)
    if str(path).startswith(str(Path.cwd())):
        rv = str(path.relative_to(Path.cwd()))
        return "" if rv == "." else rv

    return str(path.absolute())


def filter_names(iterable: Iterable, *partial_names: str) -> List[str]:
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
