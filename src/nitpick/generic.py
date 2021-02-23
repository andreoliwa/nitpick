"""Generic functions and classes.

.. testsetup::

    from nitpick.generic import *
"""
import re
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, MutableMapping, Optional, Tuple, Union

import jmespath
from jmespath.parser import ParsedResult

from nitpick.constants import DOUBLE_QUOTE, PROJECT_NAME, SEPARATOR_FLATTEN, SEPARATOR_QUOTED_SPLIT, SINGLE_QUOTE
from nitpick.typedefs import JsonDict, PathOrStr


def get_subclasses(cls):
    """Recursively get subclasses of a parent class."""
    subclasses = []
    for subclass in cls.__subclasses__():
        subclasses.append(subclass)
        subclasses += get_subclasses(subclass)
    return subclasses


def flatten(dict_, parent_key="", separator=".", current_lists=None) -> JsonDict:
    """Flatten a nested dict.

    Use :py:meth:`unflatten()` to revert.

    Adapted from `this StackOverflow question <https://stackoverflow.com/a/6027615>`_.

    >>> expected = {'root.sub1': 1, 'root.sub2.deep': 3, 'sibling': False}
    >>> flatten({"root": {"sub1": 1, "sub2": {"deep": 3}}, "sibling": False}) == expected
    True
    >>> expected = {'parent."with.dot".again': True, 'parent."my.my"': 1, "parent.123": "numeric-key"}
    >>> flatten({"parent": {"with.dot": {"again": True}, "my.my": 1, 123: "numeric-key"}}) == expected
    True
    """
    if current_lists is None:
        current_lists = {}

    items = []  # type: List[Tuple[str, Any]]
    for key, value in dict_.items():
        quoted_key = f"{DOUBLE_QUOTE}{key}{DOUBLE_QUOTE}" if separator in str(key) else key
        new_key = str(parent_key) + separator + str(quoted_key) if parent_key else quoted_key
        if isinstance(value, dict):
            items.extend(flatten(value, new_key, separator, current_lists).items())
        elif isinstance(value, (list, tuple)):
            # If the value is a list or tuple, append to a previously existing list.
            existing_list = current_lists.get(new_key, [])
            existing_list.extend(list(value))
            current_lists[new_key] = existing_list

            items.append((new_key, existing_list))
        else:
            items.append((new_key, value))
    return dict(items)


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


def unflatten(dict_, separator=".", sort=True) -> OrderedDict:
    """Turn back a flattened dict created by :py:meth:`flatten()` into a nested dict.

    >>> expected = {'my': {'sub': {'path': True}, 'home': 4}, 'another': {'path': 3}}
    >>> unflatten({"my.sub.path": True, "another.path": 3, "my.home": 4}) == expected
    True
    >>> unflatten({"repo": "conflicted key", "repo.name": "?", "repo.path": "?"})
    Traceback (most recent call last):
      ...
    TypeError: 'str' object does not support item assignment
    """
    items: OrderedDict = OrderedDict()
    for root_key, root_value in sorted(dict_.items()) if sort else dict_.items():
        all_keys = quoted_split(root_key, separator)
        sub_items = items
        for key in all_keys[:-1]:
            try:
                sub_items = sub_items[key]
            except KeyError:
                sub_items[key] = OrderedDict()
                sub_items = sub_items[key]

        sub_items[all_keys[-1]] = root_value

    return items


class MergeDict:
    """A dictionary that can merge other dictionaries into it."""

    def __init__(self, original_dict: JsonDict = None) -> None:
        self._all_flattened: OrderedDict = OrderedDict()
        self._current_lists: Dict[str, Iterable] = {}
        self.add(original_dict or {})

    def add(self, other: JsonDict) -> None:
        """Add another dictionary to the existing data."""
        flattened_other = flatten(other, separator=SEPARATOR_FLATTEN, current_lists=self._current_lists)
        self._all_flattened.update(flattened_other)

    def merge(self, sort=True) -> JsonDict:
        """Merge the dictionaries, replacing values with identical keys and extending lists."""
        return unflatten(self._all_flattened, separator=SEPARATOR_FLATTEN, sort=sort)


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
    >>> find_object_by_key(None, "fruit", "pear")
    {}
    """
    for obj in list_ or []:
        if obj.get(search_key) == search_value:
            return obj
    return {}


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


@lru_cache()
def relative_to_current_dir(path_or_str: Optional[PathOrStr]) -> str:
    """Return a relative path to the current dir or an absolute path."""
    if not path_or_str:
        return ""

    path = Path(path_or_str)
    if str(path).startswith(str(Path.cwd())):
        return str(path.relative_to(Path.cwd())).lstrip(".")

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
