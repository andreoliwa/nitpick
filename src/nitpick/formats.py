"""Configuration file formats."""
import abc
import io
import json
import logging
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable, List, Optional, Type, Union

import dictdiffer
import toml
from ruamel.yaml import YAML, RoundTripRepresenter
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from sortedcontainers import SortedDict

from nitpick.generic import flatten, unflatten
from nitpick.typedefs import JsonDict, PathOrStr, YamlData

LOGGER = logging.getLogger(__name__)


class Comparison:
    """A comparison between two dictionaries, computing missing items and differences."""

    def __init__(
        self,
        actual: Union[JsonDict, YamlData, "BaseFormat"],
        expected: Union[JsonDict, YamlData, "BaseFormat"],
        format_class: Type["BaseFormat"],
    ) -> None:
        self.flat_actual = self._normalize_value(actual)
        self.flat_expected = self._normalize_value(expected)

        self.format_class = format_class

        self.missing_format = None  # type: Optional[BaseFormat]
        self.missing_dict = {}  # type: Union[JsonDict, YamlData]

        self.diff_format = None  # type: Optional[BaseFormat]
        self.diff_dict = {}  # type: Union[JsonDict, YamlData]

    @staticmethod
    def _normalize_value(value: Union[JsonDict, YamlData, "BaseFormat"]) -> JsonDict:
        if isinstance(value, BaseFormat):
            dict_value = value.as_data  # type: JsonDict
        else:
            dict_value = value
        return flatten(dict_value)

    def set_missing(self, missing_dict):
        """Set the missing dict and corresponding format."""
        if not missing_dict:
            return
        self.missing_dict = missing_dict
        if self.format_class:
            self.missing_format = self.format_class(data=missing_dict)

    def set_diff(self, diff_dict):
        """Set the diff dict and corresponding format."""
        if not diff_dict:
            return
        self.diff_dict = diff_dict
        if self.format_class:
            self.diff_format = self.format_class(data=diff_dict)

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

        LOGGER.warning("Err... this is unexpected, please open an issue: key=%s raw_expected=%s", key, raw_expected)


class BaseFormat(metaclass=abc.ABCMeta):
    """Base class for configuration file formats.

    :param path: Path of the config file to be loaded.
    :param string: Config in string format.
    :param data: Config data in Python format (dict, YAMLFormat, TOMLFormat instances).
    :param ignore_keys: List of keys to ignore when using the comparison methods.
    """

    def __init__(
        self,
        *,
        path: PathOrStr = None,
        string: str = None,
        data: Union[JsonDict, YamlData, "BaseFormat"] = None,
        ignore_keys: List[str] = None
    ) -> None:
        self.path = path
        self._string = string
        self._data = data
        if path is None and string is None and data is None:
            raise RuntimeError("Inform at least one argument: path, string or data")

        self._ignore_keys = ignore_keys or []
        self._reformatted = None  # type: Optional[str]
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
    def as_data(self) -> Union[JsonDict, YamlData]:
        """String content converted to a Python data structure (a dict, YAML data, etc.)."""
        if self._data is None:
            self.load()
        return self._data or {}

    @property
    def reformatted(self) -> str:
        """Reformat the configuration dict as a new string (it might not match the original string/file contents)."""
        if self._reformatted is None:
            self.load()
        return self._reformatted or ""

    @classmethod
    def cleanup(cls, *args: List[Any]) -> List[Any]:
        """Cleanup similar values according to the specific format. E.g.: YAMLFormat accepts 'True' or 'true'."""
        return list(*args)

    def _create_comparison(self, expected: Union[JsonDict, YamlData, "BaseFormat"]):
        if not self._ignore_keys:
            return Comparison(self.as_data or {}, expected or {}, self.__class__)

        actual_original = self.as_data or {}  # type: Union[JsonDict, YamlData]
        actual_copy = actual_original.copy() if isinstance(actual_original, dict) else actual_original

        expected_original = expected or {}  # type: Union[JsonDict, YamlData, "BaseFormat"]
        if isinstance(expected_original, dict):
            expected_copy = expected_original.copy()
        elif isinstance(expected_original, BaseFormat):
            expected_copy = expected_original.as_data.copy()
        else:
            expected_copy = expected_original
        for key in self._ignore_keys:
            actual_copy.pop(key, None)
            expected_copy.pop(key, None)
        return Comparison(actual_copy, expected_copy, self.__class__)

    def compare_with_flatten(self, expected: Union[JsonDict, "BaseFormat"] = None) -> Comparison:
        """Compare two flattened dictionaries and compute missing and different items."""
        comparison = self._create_comparison(expected)
        if comparison.flat_expected.items() <= comparison.flat_actual.items():
            return comparison

        comparison.set_missing(
            unflatten({k: v for k, v in comparison.flat_expected.items() if k not in comparison.flat_actual})
        )
        comparison.set_diff(
            unflatten(
                {
                    k: v
                    for k, v in comparison.flat_expected.items()
                    if k in comparison.flat_actual and comparison.flat_expected[k] != comparison.flat_actual[k]
                }
            )
        )
        return comparison

    def compare_with_dictdiffer(
        self, expected: Union[JsonDict, "BaseFormat"] = None, transform_function: Callable = None
    ) -> Comparison:
        """Compare two structures and compute missing and different items using ``dictdiffer``."""
        comparison = self._create_comparison(expected)

        comparison.missing_dict = SortedDict()
        comparison.diff_dict = SortedDict()
        for diff_type, key, values in dictdiffer.diff(comparison.flat_actual, comparison.flat_expected):
            if diff_type == dictdiffer.ADD:
                comparison.missing_dict.update(dict(values))
            elif diff_type == dictdiffer.CHANGE:
                raw_actual, raw_expected = values
                actual_value, expected_value = comparison.format_class.cleanup(raw_actual, raw_expected)
                if actual_value != expected_value:
                    comparison.update_pair(key, raw_expected)

        missing = transform_function(comparison.missing_dict) if transform_function else comparison.missing_dict
        comparison.set_missing(missing)
        comparison.set_diff(comparison.diff_dict)
        return comparison


class TOMLFormat(BaseFormat):
    """TOML configuration format."""

    @staticmethod
    def group_name_for(file_name: str) -> str:
        """Return a TOML group name for a file name.

        If the file name begins with a dot, remove it.
        Otherwise an error is raised: TomlDecodeError: Invalid group name 'xxx'. Try quoting it.
        """
        return file_name.lstrip(".")

    def load(self) -> bool:
        """Load a TOML file by its path, a string or a dict."""
        if self._loaded:
            return False
        if self.path is not None:
            self._string = Path(self.path).read_text()
        if self._string is not None:
            self._data = toml.loads(self._string, _dict=OrderedDict)
        if self._data is not None:
            if isinstance(self._data, BaseFormat):
                self._reformatted = self._data.reformatted
            else:
                self._reformatted = toml.dumps(self._data)
        self._loaded = True
        return True


class YAMLFormat(BaseFormat):
    """YAML configuration format."""

    def load(self) -> bool:
        """Load a YAML file by its path, a string or a dict."""
        if self._loaded:
            return False

        yaml = YAML()
        yaml.map_indent = 2
        yaml.sequence_indent = 4
        yaml.sequence_dash_offset = 2

        if self.path is not None:
            self._string = Path(self.path).read_text()
        if self._string is not None:
            self._data = yaml.load(io.StringIO(self._string))
        if self._data is not None:
            if isinstance(self._data, BaseFormat):
                self._reformatted = self._data.reformatted
            else:
                output = io.StringIO()
                yaml.dump(self._data, output)
                self._reformatted = output.getvalue()

        self._loaded = True
        return True

    @property
    def as_data(self) -> CommentedMap:
        """On YAML, this dict is a special object with comments and ordered keys."""
        return super().as_data

    @property
    def as_list(self) -> CommentedSeq:
        """A list of dicts. On YAML, ``as_data`` might contain a ``list``. This property is just a proxy for typing."""
        return self.as_data

    @classmethod
    def cleanup(cls, *args: List[Any]) -> List[Any]:
        """A boolean "True" or "true" might have the same effect on YAML."""
        return [str(value).lower() if isinstance(value, (int, float, bool)) else value for value in args]


RoundTripRepresenter.add_representer(SortedDict, RoundTripRepresenter.represent_dict)


class JSONFormat(BaseFormat):
    """JSON configuration format."""

    def load(self) -> bool:
        """Load a JSON file by its path, a string or a dict."""
        if self._loaded:
            return False
        if self.path is not None:
            self._string = Path(self.path).read_text()
        if self._string is not None:
            self._data = json.loads(self._string, object_pairs_hook=OrderedDict)
        if self._data is not None:
            if isinstance(self._data, BaseFormat):
                self._reformatted = self._data.reformatted
            else:
                self._reformatted = json.dumps(self._data, sort_keys=True, indent=2)
        self._loaded = True
        return True

    @classmethod
    def cleanup(cls, *args: List[Any]) -> List[Any]:
        """Cleanup similar values according to the specific format. E.g.: YAMLFormat accepts 'True' or 'true'."""
        return list(args)
