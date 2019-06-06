# -*- coding: utf-8 -*-
"""Generic functions and classes.

.. testsetup::

    from flake8_nitpick.generic import *
"""
import collections
from pathlib import Path
from typing import Any, Iterable, List, MutableMapping, Optional, Tuple, Union

import jmespath
from jmespath.parser import ParsedResult

from flake8_nitpick.typedefs import PathOrStr


def get_subclasses(cls):
    """Recursively get subclasses of a parent class."""
    subclasses = []
    for subclass in cls.__subclasses__():
        subclasses.append(subclass)
        subclasses += get_subclasses(subclass)
    return subclasses


def flatten(dict_, parent_key="", separator="."):
    """Flatten a nested dict.

    Use :py:meth:`unflatten()` to revert.

    >>> flatten({"root": {"sub1": 1, "sub2": {"deep": 3}}, "sibling": False}) == {'root.sub1': 1, 'root.sub2.deep': 3, 'sibling': False}
    True
    """
    items = []
    for key, value in dict_.items():
        new_key = parent_key + separator + key if parent_key else key
        if isinstance(value, collections.abc.MutableMapping):
            items.extend(flatten(value, new_key, separator=separator).items())
        else:
            items.append((new_key, value))
    return dict(items)


def unflatten(dict_, separator=".") -> collections.OrderedDict:
    """Turn back a flattened dict created by :py:meth:`flatten()` into a nested dict.

    >>> unflatten({"my.sub.path": True, "another.path": 3, "my.home": 4}) == {'my': {'sub': {'path': True}, 'home': 4}, 'another': {'path': 3}}
    True
    """
    items = collections.OrderedDict()  # type: collections.OrderedDict[str, Any]
    for k, v in sorted(dict_.items()):
        keys = k.split(separator)
        sub_items = items
        for ki in keys[:-1]:
            try:
                sub_items = sub_items[ki]
            except KeyError:
                sub_items[ki] = collections.OrderedDict()
                sub_items = sub_items[ki]

        sub_items[keys[-1]] = v

    return items


def climb_directory_tree(starting_path: PathOrStr, file_patterns: Iterable[str]) -> Optional[List[Path]]:
    """Climb the directory tree looking for file patterns."""
    current_dir = Path(starting_path).absolute()  # type: Path
    if current_dir.is_file():
        current_dir = current_dir.parent

    while current_dir.root != str(current_dir):
        for root_file in file_patterns:
            found_files = list(current_dir.glob(root_file))
            if found_files:
                return found_files
        current_dir = current_dir.parent
    return None


def find_object_by_key(list_: List[dict], search_key: str, search_value: Any) -> dict:
    """Find an object in a list, using a key/value pair to search.

    >>> fruits = [{"id": 1, "fruit": "banana"}, {"id": 2, "fruit": "apple"}, {"id": 3, "fruit": "mango"}]
    >>> find_object_by_key(fruits, "id", 1) == {'id': 1, 'fruit': 'banana'}
    True
    >>> find_object_by_key(fruits, "fruit", "banana") == {'id': 1, 'fruit': 'banana'}
    True
    >>> find_object_by_key(fruits, "fruit", "pear")
    {}
    >>> find_object_by_key(fruits, "fruit", "mango") == {'id': 3, 'fruit': 'mango'}
    True
    """
    for obj in list_:
        if obj.get(search_key) == search_value:
            return obj
    return {}


def rmdir_if_empty(path_or_str: PathOrStr):
    """Remove the directory if empty."""
    path = Path(path_or_str)
    if not path.exists():
        return

    try:
        has_items = next(path.iterdir(), False)
        if has_items is False:
            # If the directory has no more files/directories inside, try to remove the parent.
            path.rmdir()
    except FileNotFoundError:
        # If any removal attempt fails, just ignore it. Some other flake8 thread might have deleted the directory.
        pass


def search_dict(jmespath_expression: Union[ParsedResult, str], data: MutableMapping[str, Any], default: Any) -> Any:
    """Search a dictionary using a JMESPath expression, and returning a default value.

    >>> data = {"root": {"app": [1, 2], "test": "something"}}
    >>> search_dict("root.app", data, None)
    [1, 2]
    >>> search_dict("root.test", data, None)
    'something'
    >>> search_dict("root.unknown", data, "")
    ''
    >>> search_dict("root.unknown", data, None)

    >>> search_dict(jmespath.compile("root.app"), data, [])
    [1, 2]
    >>> search_dict(jmespath.compile("root.whatever"), data, "xxx")
    'xxx'

    :param jmespath_expression: A compiled JMESPath expression or a string with an expression.
    :param data: The dictionary to be searched.
    :param default: Default value in case nothing is found.
    :return: The object that was found or the default value.
    """
    if isinstance(jmespath_expression, str):
        rv = jmespath.search(jmespath_expression, data)
    else:
        rv = jmespath_expression.search(data)
    return rv or default


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
    """
    return url.startswith("http")
