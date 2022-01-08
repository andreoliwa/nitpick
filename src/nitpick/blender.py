"""Dictionary blender and configuration file formats.

.. testsetup::

    from nitpick.generic import *
"""
import abc
import json
import re
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, MutableMapping, Optional, Tuple, Type, Union

import dictdiffer
import jmespath
import toml
import tomlkit
from autorepr import autorepr
from jmespath.parser import ParsedResult
from more_itertools import always_iterable
from ruamel.yaml import YAML, RoundTripRepresenter, StringIO
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from sortedcontainers import SortedDict

from nitpick.constants import DOT, DOUBLE_QUOTE, SEPARATOR_FLATTEN, SEPARATOR_QUOTED_SPLIT, SINGLE_QUOTE
from nitpick.typedefs import JsonDict, PathOrStr, YamlObject, YamlValue

DICT_CLASSES = (dict, SortedDict, OrderedDict, CommentedMap)
LIST_CLASSES = (list, tuple)


def compare_lists_with_dictdiffer(actual: List[Any], expected: List[Any]) -> List:
    """Compare two lists using dictdiffer."""
    additions_and_changes = [change for change in dictdiffer.diff(actual, expected) if change[0] != "remove"]
    if additions_and_changes:
        try:
            changed_dict = dictdiffer.patch(additions_and_changes, {})
            return list(changed_dict.values())
        except KeyError:
            return expected
    return []


def search_json(
    json_data: Union[MutableMapping[str, Any], List[Any]],
    jmespath_expression: Union[ParsedResult, str],
    default: Any = None,
) -> Any:
    """Search a dictionary or list using a JMESPath expression. Return a default value if not found.

    >>> data = {"root": {"app": [1, 2], "test": "something"}}
    >>> search_json(data, "root.app", None)
    [1, 2]
    >>> search_json(data, "root.test", None)
    'something'
    >>> search_json(data, "root.unknown", "")
    ''
    >>> search_json(data, "root.unknown", None)

    >>> search_json(data, "root.unknown")

    >>> search_json(data, jmespath.compile("root.app"), [])
    [1, 2]
    >>> search_json(data, jmespath.compile("root.whatever"), "xxx")
    'xxx'

    :param jmespath_expression: A compiled JMESPath expression or a string with an expression.
    :param json_data: The dictionary to be searched.
    :param default: Default value in case nothing is found.
    :return: The object that was found or the default value.
    """
    if isinstance(jmespath_expression, str):
        rv = jmespath.search(jmespath_expression, json_data)
    else:
        rv = jmespath_expression.search(json_data)
    return rv or default


def search_element_by_unique_key(  # pylint: disable=too-many-locals
    actual_list: List[Any], expected_list: List[Any], nested_key: str, parent_key: str = ""
) -> Tuple[List, List]:
    """Search an element in a list with a JMES expression representing the unique key.

    :return: Tuple with 2 lists: new elements only and the whole new list.
    """
    jmes_search_key = f"{parent_key}[].{nested_key}" if parent_key else nested_key

    actual_keys = search_json(actual_list, f"[].{jmes_search_key}", [])
    if not actual_keys:
        # There are no actual keys in the current YAML: let's insert the whole expected block
        return expected_list, actual_list + expected_list

    actual_indexes = {
        key: index for index, element in enumerate(actual_list) for key in search_json(element, jmes_search_key, [])
    }

    display = []
    replace = actual_list.copy()
    for element in expected_list:
        expected_keys = search_json(element, jmes_search_key, None)
        if not expected_keys:
            # There are no expected keys in this current element: let's insert the whole element
            display.append(element)
            replace.append(element)
            continue

        for expected_key in always_iterable(expected_keys or []):
            if expected_key not in actual_keys:
                display.append(element)
                replace.append(element)
                continue

            # If the element exists, compare with the actual one (by index)
            index = actual_indexes.get(expected_key, None)
            if index is None:
                continue

            jmes_nested = f"{parent_key}[?{nested_key}=='{expected_key}']"
            actual_nested = search_json(actual_list[index], jmes_nested, [])
            expected_nested = search_json(element, jmes_nested, [{}])
            diff_nested = compare_lists_with_dictdiffer(actual_nested, expected_nested)
            if not diff_nested:
                continue

            element[parent_key] = diff_nested
            display.append(element)

            new_block = actual_list[index].copy()
            for nested_index, obj in enumerate(actual_list[index][parent_key]):
                if obj == actual_nested[0]:
                    new_block[parent_key][nested_index] = diff_nested[0]
                    break
            replace[index] = new_block

    return display, replace


def set_key_if_not_empty(dict_: JsonDict, key: str, value: Any) -> None:
    """Update the dict if the value is valid."""
    if not value:
        return
    dict_[key] = value


def quoted_split(string_: str, separator=DOT) -> List[str]:
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


def unflatten(dict_, separator=DOT, sort=True) -> OrderedDict:
    """Turn back a flattened dict created by :py:meth:`flatten()` into a nested dict.

    >>> expected = {'my': {'sub': {'path': True}, 'home': 4}, 'another': {'path': 3}}
    >>> unflatten({"my.sub.path": True, "another.path": 3, "my.home": 4}) == expected
    True
    >>> unflatten({"repo": "conflicted key", "repo.name": "?", "repo.path": "?"})
    Traceback (most recent call last):
      ...
    TypeError: 'str' object does not support item assignment
    """
    # TODO: move flatten() and unflatten() to DictBlender: they depend on each other and keep state between calls.
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


class DictBlender:
    """A blender of dictionaries: keep adding dictionaries and mix them all at the end.

    .. note::

        This class intentionally doesn't inherit from the standard ``dict()``.
        It's an unnecessary hassle to override and deal with all those magic dunder methods.
    """

    def __init__(
        self, original_dict: JsonDict = None, *, extend_lists=True, separator: str = SEPARATOR_FLATTEN
    ) -> None:
        self._current_flat_dict: OrderedDict = OrderedDict()
        self._current_lists: Dict[str, List[Any]] = {}
        self.extend_lists = extend_lists
        self.separator = separator
        self.add(original_dict or {})

    def add(self, other: JsonDict) -> None:
        """Add another dictionary to the existing data."""
        self._current_flat_dict.update(self._flatten(other))

    def _flatten(self, other_dict: JsonDict, parent_key="") -> JsonDict:
        """Flatten a nested dict.

        Adapted from `this StackOverflow question <https://stackoverflow.com/a/6027615>`_.
        """
        items: List[Tuple[str, Any]] = []
        for key, value in other_dict.items():
            quoted_key = f"{DOUBLE_QUOTE}{key}{DOUBLE_QUOTE}" if self.separator in str(key) else key
            new_key = str(parent_key) + self.separator + str(quoted_key) if parent_key else quoted_key
            if isinstance(value, dict):
                flat_dict = self._flatten(value, new_key)
                items.extend(flat_dict.items())
            elif isinstance(value, (list, tuple)) and self.extend_lists:
                # If the value is a list or tuple, append to a previously existing list.
                existing_list = self._current_lists.get(new_key, [])
                existing_list.extend(list(value))
                self._current_lists[new_key] = existing_list

                items.append((new_key, existing_list))
            else:
                items.append((new_key, value))
        return dict(items)

    @property
    def flat_dict(self):
        """Return a flat dictionary with the current content."""
        return self._current_flat_dict

    def mix(self, sort=True) -> JsonDict:
        """Mix all dictionaries, replacing values with identical keys and extending lists."""
        return unflatten(self._current_flat_dict, self.separator, sort)


class Comparison:
    """A comparison between two dictionaries, computing missing items and differences."""

    def __init__(
        self,
        actual: JsonDict,
        expected: JsonDict,
        doc_class: Type["BaseDoc"],
    ) -> None:
        self.flat_actual = DictBlender(actual, separator=DOT).flat_dict
        self.flat_expected = DictBlender(expected, separator=DOT).flat_dict

        self.doc_class = doc_class

        self.missing_dict: JsonDict = {}
        self.diff_dict: JsonDict = {}
        self.replace_dict: JsonDict = {}

    @property
    def missing(self) -> Optional["BaseDoc"]:
        """Missing data."""
        if not self.missing_dict:
            return None
        return self.doc_class(obj=self.missing_dict)

    @property
    def diff(self) -> Optional["BaseDoc"]:
        """Different data."""
        if not self.diff_dict:
            return None
        return self.doc_class(obj=self.diff_dict)

    @property
    def replace(self) -> Optional["BaseDoc"]:
        """Data to be replaced."""
        if not self.replace_dict:
            return None
        return self.doc_class(obj=self.replace_dict)

    @property
    def has_changes(self) -> bool:
        """Return True is there is a difference or something missing."""
        return bool(self.missing or self.diff or self.replace)


class BaseDoc(metaclass=abc.ABCMeta):
    """Base class for configuration file formats.

    :param path: Path of the config file to be loaded.
    :param string: Config in string format.
    :param obj: Config object (Python dict, YamlDoc, TomlDoc instances).
    :param ignore_keys: List of keys to ignore when using the comparison methods.
    """

    __repr__ = autorepr(["path"])

    def __init__(
        self, *, path: PathOrStr = None, string: str = None, obj: JsonDict = None, ignore_keys: List[str] = None
    ) -> None:
        self.path = path
        self._string = string
        self._object = obj

        self._ignore_keys = ignore_keys or []
        self._reformatted: Optional[str] = None
        self._loaded = False

    @abc.abstractmethod
    def load(self):
        """Load the configuration from a file, a string or a dict."""

    @property
    def as_string(self) -> str:
        """Contents of the file or the original string provided when the instance was created."""
        if self._string is None:
            self.load()
        return self._string or ""

    @property
    def as_object(self) -> Dict:
        """String content converted to a Python object (dict, YAML object instance, etc.)."""
        if self._object is None:
            self.load()
        return self._object or {}

    @property
    def reformatted(self) -> str:
        """Reformat the configuration dict as a new string (it might not match the original string/file contents)."""
        if self._reformatted is None:
            self.load()
        return self._reformatted or ""

    @classmethod
    def cleanup(cls, *args: List[Any]) -> List[Any]:
        """Cleanup similar values according to the specific format. E.g.: YamlDoc accepts 'True' or 'true'."""
        return list(*args)

    def _create_comparison(self, expected: JsonDict):
        if not self._ignore_keys:
            return Comparison(self.as_object or {}, expected or {}, self.__class__)

        actual_original = self.as_object or {}
        actual_copy = actual_original.copy() if isinstance(actual_original, dict) else actual_original

        expected_original: JsonDict = expected or {}
        if isinstance(expected_original, dict):
            expected_copy: JsonDict = expected_original.copy()
        elif isinstance(expected_original, BaseDoc):
            expected_copy = expected_original.as_object.copy()  # type: ignore[attr-defined]
        else:
            expected_copy = expected_original
        for key in self._ignore_keys:
            actual_copy.pop(key, None)
            expected_copy.pop(key, None)
        return Comparison(actual_copy, expected_copy, self.__class__)

    def compare_with_flatten(self, expected: JsonDict = None, unique_keys: JsonDict = None) -> Comparison:
        """Compare two flattened dictionaries and compute missing and different items."""
        comparison = self._create_comparison(expected or {})
        if comparison.flat_expected.items() <= comparison.flat_actual.items():
            return comparison

        # TODO: this can be a field in a Pydantic model called SpecialConfig.search_unique_key
        #  the method should receive SpecialConfig instead of unique_keys
        unique_keys = unique_keys or {}

        diff: JsonDict = {}
        missing: JsonDict = {}
        replace: JsonDict = {}
        for key, expected_value in comparison.flat_expected.items():
            if key not in comparison.flat_actual:
                missing[key] = expected_value
                continue

            actual = comparison.flat_actual[key]
            if isinstance(expected_value, list):
                try:
                    nested_key, parent_key = unique_keys.get(key, ("", ""))
                except ValueError:
                    nested_key = ""
                    parent_key = ""
                if nested_key:
                    new_elements, whole_list = search_element_by_unique_key(
                        actual, expected_value, nested_key, parent_key
                    )
                    if new_elements:
                        set_key_if_not_empty(missing, key, new_elements)
                        set_key_if_not_empty(replace, key, whole_list)
                else:
                    set_key_if_not_empty(diff, key, compare_lists_with_dictdiffer(actual, expected_value))
            elif expected_value != actual:
                set_key_if_not_empty(diff, key, expected_value)

        comparison.missing_dict = unflatten(missing)
        comparison.diff_dict = unflatten(diff)
        comparison.replace_dict = unflatten(replace)
        return comparison


class InlineTableTomlDecoder(toml.TomlDecoder):  # type: ignore[name-defined]
    """A hacky decoder to work around some bug (or unfinished work) in the Python TOML package.

    https://github.com/uiri/toml/issues/362.
    """

    def get_empty_inline_table(self):
        """Hackity hack for a crappy unmaintained package.

        Total lack of respect, the guy doesn't even reply: https://github.com/uiri/toml/issues/361
        """
        return self.get_empty_table()


class TomlDoc(BaseDoc):
    """TOML configuration format."""

    def __init__(
        self,
        *,
        path: PathOrStr = None,
        string: str = None,
        obj: JsonDict = None,
        ignore_keys: List[str] = None,
        use_tomlkit=False,
    ) -> None:
        super().__init__(path=path, string=string, obj=obj, ignore_keys=ignore_keys)
        self.use_tomlkit = use_tomlkit

    def load(self) -> bool:
        """Load a TOML file by its path, a string or a dict."""
        if self._loaded:
            return False
        if self.path is not None:
            self._string = Path(self.path).read_text(encoding="UTF-8")
        if self._string is not None:
            # TODO: I tried to replace toml by tomlkit, but lots of tests break.
            #  The conversion to OrderedDict is not being done recursively (although I'm not sure this is a problem).
            if self.use_tomlkit:
                self._object = OrderedDict(tomlkit.loads(self._string))
            else:
                self._object = toml.loads(self._string, decoder=InlineTableTomlDecoder(OrderedDict))  # type: ignore[call-arg,assignment]
        if self._object is not None:
            if isinstance(self._object, BaseDoc):
                self._reformatted = self._object.reformatted
            else:
                # TODO: tomlkit.dumps() renders comments and I didn't find a way to turn this off,
                #  but comments are being lost when the TOML plugin does dict comparisons.
                if self.use_tomlkit:
                    self._reformatted = tomlkit.dumps(OrderedDict(self._object), sort_keys=True)
                else:
                    self._reformatted = toml.dumps(self._object)
        self._loaded = True
        return True


def traverse_toml_tree(document: tomlkit.TOMLDocument, dictionary):
    """Traverse a TOML document recursively and change values, keeping its formatting and comments."""
    for key, value in dictionary.items():
        if isinstance(value, (dict, OrderedDict)):
            if key in document:
                traverse_toml_tree(document[key], value)
            else:
                document.add(key, value)
        else:
            document[key] = value


class SensibleYAML(YAML):
    """YAML with sensible defaults but an inefficient dump to string.

    `Output of dump() as a string
    <https://yaml.readthedocs.io/en/latest/example.html#output-of-dump-as-a-string>`_
    """

    def __init__(self, *, typ=None, pure=False, output=None, plug_ins=None):
        super().__init__(typ=typ, pure=pure, output=output, plug_ins=plug_ins)
        self.map_indent = 2
        self.sequence_indent = 4
        self.sequence_dash_offset = 2
        self.preserve_quotes = True

    def loads(self, string: str):
        """Load YAML from a string... that unusual use case in a world of files only."""
        return self.load(StringIO(string))

    def dumps(self, data) -> str:
        """Dump to a string... who would want such a thing? One can dump to a file or stdout."""
        output = StringIO()
        self.dump(data, output, transform=None)
        return output.getvalue()


class YamlDoc(BaseDoc):
    """YAML configuration format."""

    updater: SensibleYAML

    def load(self) -> bool:
        """Load a YAML file by its path, a string or a dict."""
        if self._loaded:
            return False

        self.updater = SensibleYAML()

        if self.path is not None:
            self._string = Path(self.path).read_text(encoding="UTF-8")
        if self._string is not None:
            self._object = self.updater.loads(self._string)
        if self._object is not None:
            if isinstance(self._object, BaseDoc):
                self._reformatted = self._object.reformatted
            else:
                self._reformatted = self.updater.dumps(self._object)

        self._loaded = True
        return True

    @property
    def as_object(self) -> CommentedMap:
        """On YAML, this dict is a special object with comments and ordered keys."""
        return super().as_object

    @property
    def as_list(self) -> CommentedSeq:
        """A list of dicts, for typing purposes. On YAML, ``as_object`` might contain a ``list``."""
        return self.as_object

    @classmethod
    def cleanup(cls, *args: List[Any]) -> List[Any]:
        """A boolean "True" or "true" might have the same effect on YAML."""
        return [str(value).lower() if isinstance(value, (int, float, bool)) else value for value in args]


for dict_class in (SortedDict, OrderedDict):
    RoundTripRepresenter.add_representer(dict_class, RoundTripRepresenter.represent_dict)


def is_scalar(value: YamlValue) -> bool:
    """Return True if the value is NOT a dict or a list."""
    return not isinstance(value, LIST_CLASSES + DICT_CLASSES)


def traverse_yaml_tree(yaml_obj: YamlObject, change: Union[JsonDict, OrderedDict]):
    """Traverse a YAML document recursively and change values, keeping its formatting and comments."""
    for key, value in change.items():
        if key not in yaml_obj:
            if isinstance(yaml_obj, dict):
                yaml_obj[key] = value
            else:
                # Key doesn't exist: we can insert the whole nested OrderedDict at once, no regrets
                last_pos = len(yaml_obj.keys()) + 1
                yaml_obj.insert(last_pos, key, value)
            continue

        if is_scalar(value):
            yaml_obj[key] = value
        elif isinstance(value, DICT_CLASSES):
            traverse_yaml_tree(yaml_obj[key], value)
        elif isinstance(value, list):
            _traverse_yaml_list(yaml_obj, key, value)


def _traverse_yaml_list(yaml_obj: YamlObject, key: str, value: List[YamlValue]):
    for index, element in enumerate(value):
        insert: bool = index >= len(yaml_obj[key])

        if not insert and is_scalar(yaml_obj[key][index]):
            # If the original object is scalar, replace it with whatever element;
            # without traversing, even if it's a dict
            yaml_obj[key][index] = element
            continue

        if insert:
            yaml_obj[key].append(element)
            continue

        if is_scalar(element):
            yaml_obj[key][index] = element
        else:
            traverse_yaml_tree(yaml_obj[key][index], element)  # type: ignore # mypy kept complaining about the Union


class JsonDoc(BaseDoc):
    """JSON configuration format."""

    def load(self) -> bool:
        """Load a JSON file by its path, a string or a dict."""
        if self._loaded:
            return False
        if self.path is not None:
            self._string = Path(self.path).read_text(encoding="UTF-8")
        if self._string is not None:
            self._object = json.loads(self._string, object_pairs_hook=OrderedDict)
        if self._object is not None:
            if isinstance(self._object, BaseDoc):
                self._reformatted = self._object.reformatted
            else:
                # Every file should end with a blank line
                self._reformatted = json.dumps(self._object, sort_keys=True, indent=2) + "\n"
        self._loaded = True
        return True

    @classmethod
    def cleanup(cls, *args: List[Any]) -> List[Any]:
        """Cleanup similar values according to the specific format. E.g.: YamlDoc accepts 'True' or 'true'."""
        return list(args)
