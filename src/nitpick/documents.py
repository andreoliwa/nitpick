"""Configuration file formats."""
import abc
import json
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, Union

import dictdiffer
import toml
import tomlkit
from autorepr import autorepr
from loguru import logger
from ruamel.yaml import YAML, RoundTripRepresenter, StringIO
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from sortedcontainers import SortedDict

from nitpick.generic import flatten, search_dict, unflatten
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


def search_element_by_unique_key(actual: List[Any], expected: List[Any], jmes_search_key: str) -> List:
    """Search an element in a list with a JMES expression representing the unique key."""
    actual_keys = set(search_dict(f"[].{jmes_search_key}", actual, []))
    if not actual_keys:
        # There are no actual keys in the current YAML: let's insert the whole expected block
        return expected

    new_elements = []
    for element in expected:
        expected_ids = search_dict(jmes_search_key, element, [])
        if not expected_ids:
            # There are no expected keys in this current element: let's insert the whole element
            new_elements.append(element)
            continue

        for expected_hook_id in search_dict(jmes_search_key, element, []):
            if expected_hook_id not in actual_keys:
                new_elements.append(element)
                break
            # else:
            # FIXME: if hook exists, compare it and add to "diff" if different
    return new_elements


def set_key_if_not_empty(dict_: JsonDict, key: str, value: Any) -> None:
    """Update the dict if the value is valid."""
    if not value:
        return
    dict_[key] = value


class Comparison:
    """A comparison between two dictionaries, computing missing items and differences."""

    def __init__(
        self,
        actual: JsonDict,
        expected: JsonDict,
        doc_class: Type["BaseDoc"],
    ) -> None:
        self.flat_actual = self._normalize_value(actual)
        self.flat_expected = self._normalize_value(expected)

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

    @staticmethod
    def _normalize_value(value: JsonDict) -> Dict:
        if isinstance(value, BaseDoc):
            dict_value = value.as_object
        else:
            dict_value = value
        return flatten(dict_value)

    def update_pair(self, key, raw_expected):
        """Update a key on one of the comparison dicts, with its raw expected value."""
        if isinstance(key, str):
            self.diff_dict.update({key: raw_expected})
            return

        if isinstance(key, list):
            if len(key) == 4 and isinstance(key[3], int):
                _, _, new_key, index = key
                if new_key not in self.diff_dict:
                    self.diff_dict[new_key] = []
                self.diff_dict[new_key].insert(index, raw_expected)
                return
            if len(key) == 1:
                self.diff_dict.update(unflatten({key[0]: raw_expected}))
                return

        logger.warning("Err... this is unexpected, please open an issue: key={} raw_expected={}", key, raw_expected)


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

        # FIXME: this can be a field in a Pydantic model called SpecialConfig.search_unique_key
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
                unique_key = unique_keys.get(key, None)
                if unique_key:
                    new_elements = search_element_by_unique_key(actual, expected_value, unique_key)
                    set_key_if_not_empty(missing, key, new_elements)
                    if new_elements:
                        set_key_if_not_empty(replace, key, actual + new_elements)
                else:
                    set_key_if_not_empty(diff, key, compare_lists_with_dictdiffer(actual, expected_value))
            elif expected_value != actual:
                set_key_if_not_empty(diff, key, expected_value)

        comparison.missing_dict = unflatten(missing)
        comparison.diff_dict = unflatten(diff)
        comparison.replace_dict = unflatten(replace)
        return comparison

    def compare_with_dictdiffer(self, expected: JsonDict = None, transform_function: Callable = None) -> Comparison:
        """Compare two structures and compute missing and different items using ``dictdiffer``."""
        comparison = self._create_comparison(expected or {})

        missing_dict = SortedDict()
        for diff_type, key, values in dictdiffer.diff(comparison.flat_actual, comparison.flat_expected):
            if diff_type == dictdiffer.ADD:
                missing_dict.update(dict(values))
            elif diff_type == dictdiffer.CHANGE:
                raw_actual, raw_expected = values
                actual_value, expected_value = comparison.doc_class.cleanup(raw_actual, raw_expected)
                if actual_value != expected_value:
                    comparison.update_pair(key, raw_expected)

        comparison.missing_dict = transform_function(missing_dict) if transform_function else missing_dict
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
