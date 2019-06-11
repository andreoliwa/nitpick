# -*- coding: utf-8 -*-
"""Configuration file formats."""
import abc
import io
from collections import OrderedDict
from pathlib import Path
from typing import Any, List, Optional, Type, Union

import dictdiffer
import toml
from ruamel.yaml import YAML, RoundTripRepresenter
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from sortedcontainers import SortedDict

from nitpick.generic import flatten, unflatten
from nitpick.typedefs import JsonDict, PathOrStr, YamlData


class Comparison:
    """A comparison between two dictionaries, computing missing items and differences."""

    def __init__(
        self,
        actual: Union[JsonDict, YamlData, "BaseFormat"],
        expected: Union[JsonDict, YamlData, "BaseFormat"],
        format_class: Type["BaseFormat"] = None,
    ) -> None:
        self._actual = actual.as_data if isinstance(actual, BaseFormat) else actual  # type: JsonDict
        self._flat_actual = flatten(self._actual)

        self._expected = expected.as_data if isinstance(expected, BaseFormat) else expected  # type: JsonDict
        self._flat_expected = flatten(self._expected)

        self.format_class = format_class

        self.missing_format = None  # type: Optional[BaseFormat]
        self.missing_dict = None  # type: Optional[JsonDict]

        self.diff_format = None  # type: Optional[BaseFormat]
        self.diff_dict = None  # type: Optional[JsonDict]

    def compare_with_flatten(self) -> "Comparison":
        """Compare two flattened dictionaries and compute missing and different items."""
        if self._flat_expected.items() <= self._flat_actual.items():
            return self

        missing_dict = unflatten({k: v for k, v in self._flat_expected.items() if k not in self._flat_actual})
        if missing_dict:
            self.missing_dict = missing_dict
            if self.format_class:
                self.missing_format = self.format_class(data=missing_dict)

        diff_dict = unflatten(
            {
                k: v
                for k, v in self._flat_expected.items()
                if k in self._flat_actual and self._flat_expected[k] != self._flat_actual[k]
            }
        )
        if diff_dict:
            self.diff_dict = diff_dict
            if self.format_class:
                self.diff_format = self.format_class(data=diff_dict)

        return self

    def compare_with_dictdiffer(self):
        """Compare two structures and compute missing and different items using ``dictdiffer``."""
        all_missing = SortedDict()
        all_differences = SortedDict()
        for diff_type, key, values in dictdiffer.diff(self._flat_actual, self._flat_expected):
            if diff_type == dictdiffer.ADD:
                all_missing.update(dict(values))
            elif diff_type == dictdiffer.CHANGE:
                raw_actual, raw_expected = values
                actual_value, expected_value = self.format_class.cleanup(raw_actual, raw_expected)
                if actual_value != expected_value:
                    all_differences.update({key: raw_expected})

        if all_missing:
            self.missing_dict = all_missing
            if self.format_class:
                self.missing_format = self.format_class(data=all_missing)

        if all_differences:
            self.diff_dict = all_differences
            if self.format_class:
                self.diff_format = self.format_class(data=all_differences)

        return self


class BaseFormat(metaclass=abc.ABCMeta):
    """Base class for configuration file formats."""

    def __init__(self, *, path: PathOrStr = None, string: str = None, data: Union[JsonDict, YamlData] = None) -> None:
        self.path = path
        self._string = string
        self._data = data
        if path is None and string is None and data is None:
            raise RuntimeError("Inform at least one argument: path, string or data")

        self._reformatted = None  # type: Optional[str]
        self._loaded = False

    @abc.abstractmethod
    def load(self):
        """Load the configuration from a file, a string or a dict."""
        pass

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
        """Cleanup similar values according to the specific format. E.g.: Yaml accepts 'True' or 'true'."""
        return list(*args)

    def compare_with_flatten(self, expected: Union[JsonDict, "BaseFormat"] = None) -> Comparison:
        """Compare two flattened configuration dicts/objects."""
        return Comparison(self.as_data or {}, expected or {}, self.__class__).compare_with_flatten()

    def compare_with_dictdiffer(self, expected: Union[JsonDict, "BaseFormat"] = None) -> Comparison:
        """Compare two configuration objects."""
        return Comparison(self.as_data or {}, expected or {}, self.__class__).compare_with_dictdiffer()


class Toml(BaseFormat):
    """TOML configuration format."""

    def load(self) -> bool:
        """Load a TOML file by its path, a string or a dict."""
        if self._loaded:
            return False
        if self.path is not None:
            self._string = Path(self.path).read_text()
        if self._string is not None:
            self._data = toml.loads(self._string, _dict=OrderedDict)
        if self._data is not None:
            self._reformatted = toml.dumps(self._data)
        self._loaded = True
        return True


class Yaml(BaseFormat):
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