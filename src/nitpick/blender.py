"""Dictionary blender and configuration file formats.

.. testsetup::

    from nitpick.generic import *
"""
import abc
import json
import re
from collections import OrderedDict
from functools import lru_cache, partial
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import dictdiffer
import jmespath
import toml
import tomlkit
from attrs import define
from autorepr import autorepr
from jmespath.parser import ParsedResult
from ruamel.yaml import YAML, RoundTripRepresenter, StringIO
from sortedcontainers import SortedDict
from tomlkit import items

from nitpick.config import SpecialConfig
from nitpick.typedefs import ElementData, JsonDict, ListOrCommentedSeq, PathOrStr, YamlObject, YamlValue

SINGLE_QUOTE = "'"
DOUBLE_QUOTE = '"'

SEPARATOR_DOT = "."
SEPARATOR_COMMA = ","
SEPARATOR_COLON = ":"

#: Special unique separator for :py:meth:`flatten()` and :py:meth:`unflatten()`,
# to avoid collision with existing key values (e.g. the default SEPARATOR_DOT separator "." can be part of a TOML key).
SEPARATOR_FLATTEN = "$#@"

#: Special unique separator for :py:meth:`nitpick.generic.quoted_split()`.
SEPARATOR_QUOTED_SPLIT = "#$@"


def compare_lists_with_dictdiffer(
    actual: Union[List, Dict], expected: Union[List, Dict], *, return_list: bool = True
) -> Union[List, Dict]:
    """Compare two lists using dictdiffer."""
    additions_and_changes = [change for change in dictdiffer.diff(actual, expected) if change[0] != "remove"]
    if not additions_and_changes:
        return []

    try:
        changed_dict = dictdiffer.patch(additions_and_changes, {})
    except KeyError:
        return expected

    if return_list:
        return list(changed_dict.values())
    return changed_dict


def search_json(json_data: ElementData, jmespath_expression: Union[ParsedResult, str], default: Any = None) -> Any:
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
    >>> search_json(data, "")

    >>> search_json(data, None)

    :param jmespath_expression: A compiled JMESPath expression or a string with an expression.
    :param json_data: The dictionary to be searched.
    :param default: Default value in case nothing is found.
    :return: The object that was found or the default value.
    """
    if not jmespath_expression:
        return default
    if isinstance(jmespath_expression, str):
        rv = jmespath.search(jmespath_expression, json_data)
    else:
        rv = jmespath_expression.search(json_data)
    return rv or default


@define
class ElementDetail:  # pylint: disable=too-few-public-methods
    """Detailed information about an element of a list."""

    data: ElementData
    key: Union[str, List[str]]
    index: int
    scalar: bool
    compact: str

    @property
    def cast_to_dict(self) -> JsonDict:
        """Data cast to dict, for mypy."""
        return cast(JsonDict, self.data)

    @classmethod
    def from_data(cls, index: int, data: ElementData, jmes_key: str) -> "ElementDetail":
        """Create an element detail from dict data."""
        if isinstance(data, (list, dict)):
            scalar = False
            compact = json.dumps(data, sort_keys=True, separators=(SEPARATOR_COMMA, SEPARATOR_COLON))
            key = search_json(data, jmes_key)
            if not key:
                key = compact
        else:
            scalar = True
            key = compact = str(data)
        return ElementDetail(data=data, key=key, index=index, scalar=scalar, compact=compact)  # type: ignore[call-arg]


@define
class ListDetail:  # pylint: disable=too-few-public-methods
    """Detailed info about a list."""

    data: ListOrCommentedSeq
    elements: List[ElementDetail]

    @classmethod
    def from_data(cls, data: ListOrCommentedSeq, jmes_key: str) -> "ListDetail":
        """Create a list detail from list data."""
        return ListDetail(  # type: ignore[call-arg]
            data=data, elements=[ElementDetail.from_data(index, data, jmes_key) for index, data in enumerate(data)]
        )

    def find_by_key(self, desired: ElementDetail) -> Optional[ElementDetail]:
        """Find an element by key."""
        for actual in self.elements:
            if isinstance(desired.key, list):
                if set(desired.key).issubset(set(actual.key)):
                    return actual
            else:
                if desired.key == actual.key:
                    return actual
        return None


def set_key_if_not_empty(dict_: JsonDict, key: str, value: Any) -> None:
    """Update the dict if the value is valid."""
    if not value:
        return
    dict_[key] = value


def quoted_split(string_: str, separator=SEPARATOR_DOT) -> List[str]:
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


class DictBlender:
    """A blender of dictionaries: keep adding dictionaries and mix them all at the end.

    .. note::

        This class intentionally doesn't inherit from the standard ``dict()``.
        It's an unnecessary hassle to override and deal with all those magic dunder methods.

    :param dict_: Any optional dict.
    :param extend_lists: True if nested lists should be extended when the key is the same.
        False if they should be replaced.
    :param separator: Separator used for flatten and unflatten operations. Default is a unique special separator.
    :param flatten_on_add: True if dictionaries should be flattened when added (default). False to add them "as is".
    """

    def __init__(
        self,
        dict_: JsonDict = None,
        *,
        extend_lists=True,
        separator: str = SEPARATOR_FLATTEN,
        flatten_on_add: bool = True,
    ) -> None:
        self._current_flat_dict: OrderedDict = OrderedDict()
        self._current_lists: Dict[str, List[Any]] = {}
        self.extend_lists = extend_lists
        self.separator = separator
        self.flatten_on_add = flatten_on_add
        self.add(dict_ or {}, flatten_on_add=self.flatten_on_add)

    @property
    def flat_dict(self):
        """Return a flat dictionary with the current content."""
        return self._current_flat_dict

    def add(self, other: JsonDict, *, flatten_on_add: Optional[bool] = None) -> "DictBlender":
        """Add another dictionary to the existing data."""
        if flatten_on_add is None:
            flatten_on_add = self.flatten_on_add
        new_dict = self._flatten(other) if flatten_on_add else other
        self._current_flat_dict.update(new_dict)
        return self

    def _flatten(self, dict_: JsonDict, parent_key="") -> JsonDict:
        """Flatten a nested dict.

        Adapted from `this StackOverflow question <https://stackoverflow.com/a/6027615>`_.
        """
        elements: List[Tuple[str, Any]] = []
        for key, value in dict_.items():
            quoted_key = f"{DOUBLE_QUOTE}{key}{DOUBLE_QUOTE}" if self.separator in str(key) else key
            new_key = str(parent_key) + self.separator + str(quoted_key) if parent_key else quoted_key
            if isinstance(value, dict):
                elements.extend(self._flatten(value, new_key).items())
            elif isinstance(value, (list, tuple)) and self.extend_lists:
                # If the value is a list or tuple, append to a previously existing list.
                existing_list = self._current_lists.get(new_key, [])
                existing_list.extend(list(value))
                self._current_lists[new_key] = existing_list

                elements.append((new_key, existing_list))
            else:
                elements.append((new_key, value))
        return dict(elements)

    def _unflatten(self, dict_: JsonDict, sort=True) -> OrderedDict:
        """Turn back a flat dict created by the ``_flatten()`` method into a nested dict."""
        elements: OrderedDict = OrderedDict()
        for root_key, root_value in sorted(dict_.items()) if sort else dict_.items():
            all_keys = quoted_split(root_key, self.separator)
            sub_items = elements
            for key in all_keys[:-1]:
                try:
                    sub_items = sub_items[key]
                except KeyError:
                    sub_items[key] = OrderedDict()
                    sub_items = sub_items[key]

            sub_items[all_keys[-1]] = root_value

        return elements

    def mix(self, sort=True) -> JsonDict:
        """Mix all dictionaries, replacing values with identical keys and extending lists."""
        return self._unflatten(self._current_flat_dict, sort)


DotBlender = partial(DictBlender, separator=SEPARATOR_DOT, flatten_on_add=False)


class Comparison:
    """A comparison between two dictionaries, computing missing items and differences."""

    def __init__(self, actual: "BaseDoc", expected: JsonDict, special_config: SpecialConfig) -> None:
        self.flat_actual = DictBlender(actual.as_object, separator=SEPARATOR_DOT).flat_dict
        self.flat_expected = DictBlender(expected, separator=SEPARATOR_DOT).flat_dict

        self.doc_class = actual.__class__

        self.missing_dict: JsonDict = {}
        self.diff_dict: JsonDict = {}
        self.replace_dict: JsonDict = {}

        self.special_config = special_config

    @property
    def missing(self) -> Optional["BaseDoc"]:
        """Missing data."""
        if not self.missing_dict:
            return None
        return self.doc_class(obj=DotBlender(self.missing_dict).mix())

    @property
    def diff(self) -> Optional["BaseDoc"]:
        """Different data."""
        if not self.diff_dict:
            return None
        return self.doc_class(obj=DotBlender(self.diff_dict).mix())

    @property
    def replace(self) -> Optional["BaseDoc"]:
        """Data to be replaced."""
        if not self.replace_dict:
            return None
        return self.doc_class(obj=DotBlender(self.replace_dict).mix())

    @property
    def has_changes(self) -> bool:
        """Return True is there is a difference or something missing."""
        return bool(self.missing or self.diff or self.replace)

    def __call__(self) -> "Comparison":
        """Compare two flattened dictionaries and compute missing and different items."""
        if self.flat_expected.items() <= self.flat_actual.items():
            return self

        for key, expected_value in self.flat_expected.items():
            if key not in self.flat_actual:
                self.missing_dict[key] = expected_value
                self.replace_dict[key] = expected_value
                continue

            actual = self.flat_actual[key]
            if isinstance(expected_value, list):
                list_keys = self.special_config.list_keys.value.get(key, "")
                if SEPARATOR_DOT in list_keys:
                    parent_key, child_key = list_keys.rsplit(SEPARATOR_DOT, 1)
                    jmes_key = f"{parent_key}[].{child_key}"
                else:
                    parent_key = ""
                    child_key = list_keys
                    jmes_key = child_key

                self._compare_list_elements(
                    key,
                    parent_key,
                    child_key,
                    ListDetail.from_data(actual, jmes_key),
                    ListDetail.from_data(expected_value, jmes_key),
                )
            elif expected_value != actual:
                set_key_if_not_empty(self.diff_dict, key, expected_value)

        return self

    def _compare_list_elements(  # pylint: disable=too-many-arguments
        self, key: str, parent_key: str, child_key: str, actual_detail: ListDetail, expected_detail: ListDetail
    ) -> None:
        """Compare list elements by their keys or hashes."""
        display = []
        replace = actual_detail.data.copy()
        for expected_element in expected_detail.elements:
            actual_element = actual_detail.find_by_key(expected_element)
            if not actual_element:
                display.append(expected_element.data)
                replace.append(expected_element.data)
                continue

            if parent_key:
                new_block: JsonDict = self._compare_children(parent_key, child_key, actual_element, expected_element)
                if new_block:
                    display.append(expected_element.data)
                    replace[actual_element.index] = new_block
                continue

            diff = compare_lists_with_dictdiffer(
                actual_element.cast_to_dict, expected_element.cast_to_dict, return_list=False
            )
            if diff:
                new_block = cast(JsonDict, actual_element.data).copy()
                new_block.update(diff)
                display.append(new_block)
                replace[actual_element.index] = new_block

        if display:
            set_key_if_not_empty(self.missing_dict, key, display)
            set_key_if_not_empty(self.replace_dict, key, replace)

    @staticmethod
    def _compare_children(
        parent_key: str, child_key: str, actual_element: ElementDetail, expected_element: ElementDetail
    ) -> JsonDict:
        """Compare children of a JSON dict, return only the inner difference.

        E.g.: a pre-commit hook ID with different args will return a JSON only with the specific hook,
        not with all the hooks of the parent repo.
        """
        new_nested_block: JsonDict = {}
        jmes_nested = f"{parent_key}[?{child_key}=='{expected_element.key[0]}']"
        actual_nested = search_json(actual_element.data, jmes_nested, [])
        expected_nested = search_json(expected_element.data, jmes_nested, [{}])
        diff_nested = compare_lists_with_dictdiffer(actual_nested, expected_nested, return_list=True)
        if diff_nested:
            actual_data = cast(JsonDict, actual_element.data)
            expected_data = cast(JsonDict, expected_element.data)
            # TODO: set value deep down the tree (try dpath-python). parent_key = 'regions[].cities[].people'
            expected_data[parent_key] = diff_nested

            new_nested_block = actual_data.copy()
            for nested_index, obj in enumerate(actual_data[parent_key]):
                if obj == actual_nested[0]:
                    new_nested_block[parent_key][nested_index] = diff_nested[0]
                    break
        return new_nested_block


class BaseDoc(metaclass=abc.ABCMeta):
    """Base class for configuration file formats.

    :param path: Path of the config file to be loaded.
    :param string: Config in string format.
    :param obj: Config object (Python dict, YamlDoc, TomlDoc instances).
    """

    __repr__ = autorepr(["path"])

    def __init__(self, *, path: PathOrStr = None, string: str = None, obj: JsonDict = None) -> None:
        self.path = path
        self._string = string
        self._object = obj

        self._reformatted: Optional[str] = None

    @abc.abstractmethod
    def load(self) -> bool:
        """Load the configuration from a file, a string or a dict."""

    @property
    def as_string(self) -> str:
        """Contents of the file or the original string provided when the instance was created."""
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
        use_tomlkit=False,
    ) -> None:
        super().__init__(path=path, string=string, obj=obj)
        self.use_tomlkit = use_tomlkit

    @lru_cache()
    def load(self) -> bool:
        """Load a TOML file by its path, a string or a dict."""
        if self.path is not None:
            self._string = Path(self.path).read_text(encoding="UTF-8")
        if self._string is not None:
            # TODO: I tried to replace toml by tomlkit, but lots of tests break.
            #  The conversion to OrderedDict is not being done recursively (although I'm not sure this is a problem).
            if self.use_tomlkit:
                self._object = tomlkit.loads(self._string)
            else:
                self._object = toml.loads(self._string, decoder=InlineTableTomlDecoder(OrderedDict))  # type: ignore[call-arg,assignment]
        if self._object is not None:
            # TODO: tomlkit.dumps() renders comments and I didn't find a way to turn this off,
            #  but comments are being lost when the TOML plugin does dict comparisons.
            if self.use_tomlkit:
                self._reformatted = tomlkit.dumps(OrderedDict(self._object), sort_keys=True)
            else:
                self._reformatted = toml.dumps(self._object)
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

    def __init__(self):
        super().__init__()
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

    @lru_cache()
    def load(self) -> bool:
        """Load a YAML file by its path, a string or a dict."""
        self.updater = SensibleYAML()

        if self.path is not None:
            self._string = Path(self.path).read_text(encoding="UTF-8")
        if self._string is not None:
            self._object = self.updater.loads(self._string)
        if self._object is not None:
            self._reformatted = self.updater.dumps(self._object)
        return True


# Classes and their representation on ruamel.yaml
for dict_class in (SortedDict, OrderedDict, items.Table, items.InlineTable):
    RoundTripRepresenter.add_representer(dict_class, RoundTripRepresenter.represent_dict)
RoundTripRepresenter.add_representer(items.String, RoundTripRepresenter.represent_str)
for list_class in (items.Array, items.AoT):
    RoundTripRepresenter.add_representer(list_class, RoundTripRepresenter.represent_list)
RoundTripRepresenter.add_representer(items.Integer, RoundTripRepresenter.represent_int)


def is_scalar(value: YamlValue) -> bool:
    """Return True if the value is NOT a dict or a list."""
    return not isinstance(value, (list, dict))


def replace_or_add_list_element(yaml_obj: YamlObject, element: Any, key: str, index: int) -> None:
    """Replace or add a new element in a YAML sequence of mappings."""
    current = yaml_obj
    if key in yaml_obj:
        current = yaml_obj[key]

    insert: bool = index >= len(current)
    if insert:
        current.append(element)
        return

    if is_scalar(current[index]) or is_scalar(element):
        # If the original object is scalar, replace it with whatever element;
        # without traversing, even if it's a dict
        current[index] = element
        return
    if isinstance(element, dict):
        traverse_yaml_tree(current[index], element)
        return

    # At this point, value is probably a list. Set the whole list in YAML.
    current[index] = element
    return


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

        if isinstance(value, dict):
            traverse_yaml_tree(yaml_obj[key], value)
        elif isinstance(value, list):
            for index, element in enumerate(value):
                replace_or_add_list_element(yaml_obj, element, key, index)
        else:
            yaml_obj[key] = value


class JsonDoc(BaseDoc):
    """JSON configuration format."""

    @lru_cache()
    def load(self) -> bool:
        """Load a JSON file by its path, a string or a dict."""
        if self.path is not None:
            self._string = Path(self.path).read_text(encoding="UTF-8")
        if self._string is not None:
            self._object = json.loads(self._string, object_pairs_hook=OrderedDict)
        if self._object is not None:
            # Every file should end with a blank line
            self._reformatted = json.dumps(self._object, sort_keys=True, indent=2) + "\n"
        return True
