# -*- coding: utf-8 -*-
"""Configuration file formats."""
import abc
import io
from collections import OrderedDict
from pathlib import Path
from typing import Optional, Type, Union

import toml
from ruamel.yaml import YAML, RoundTripRepresenter
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from sortedcontainers import SortedDict

from nitpick.generic import flatten, unflatten
from nitpick.typedefs import JsonDict, PathOrStr


class Comparison:
    """A comparison between two dictionaries, computing missing items and differences."""

    def __init__(
        self,
        actual: Union[JsonDict, "BaseFormat"],
        expected: Union[JsonDict, "BaseFormat"],
        format_class: Type["BaseFormat"] = None,
    ) -> None:
        actual_dict = actual.as_dict if isinstance(actual, BaseFormat) else actual  # type: JsonDict
        self.actual = flatten(actual_dict)

        expected_dict = expected.as_dict if isinstance(expected, BaseFormat) else expected  # type: JsonDict
        self.expected = flatten(expected_dict)

        self.format_class = format_class

        self.missing_format = None  # type: Optional[BaseFormat]
        self.missing_dict = None  # type: Optional[JsonDict]

        self.diff_format = None  # type: Optional[BaseFormat]
        self.diff_dict = None  # type: Optional[JsonDict]

    def compare(self) -> "Comparison":
        """Compare two flattened dictionaries and compute missing and different items."""
        if self.expected.items() <= self.actual.items():
            return self

        missing_dict = unflatten({k: v for k, v in self.expected.items() if k not in self.actual})
        if missing_dict:
            self.missing_dict = missing_dict
            if self.format_class:
                self.missing_format = self.format_class(dict_=missing_dict)

        diff_dict = unflatten(
            {k: v for k, v in self.expected.items() if k in self.actual and self.expected[k] != self.actual[k]}
        )
        if diff_dict:
            self.diff_dict = diff_dict
            if self.format_class:
                self.diff_format = self.format_class(dict_=diff_dict)

        return self


class BaseFormat(metaclass=abc.ABCMeta):
    """Base class for configuration file formats."""

    def __init__(self, *, path: PathOrStr = None, string: str = None, dict_: JsonDict = None, **kwargs) -> None:
        self.path = path
        self._string = string
        self._dict = dict_
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
    def as_dict(self) -> JsonDict:
        """String content converted to a dict."""
        if self._dict is None:
            self.load()
        return self._dict or {}

    @property
    def reformatted(self) -> str:
        """Reformat the configuration dict as a new string (it might not match the original string/file contents)."""
        if self._reformatted is None:
            self.load()
        return self._reformatted or ""

    def compare_to(self, expected: Union[JsonDict, "BaseFormat"] = None) -> Comparison:
        """Compare two configuration objects."""
        return Comparison(self.as_dict or {}, expected or {}, self.__class__).compare()


class Toml(BaseFormat):
    """TOML configuration format."""

    def load(self) -> bool:
        """Load a TOML file by its path, a string or a dict."""
        if self._loaded:
            return False
        if self.path is not None:
            self._string = Path(self.path).read_text()
        if self._string is not None:
            self._dict = toml.loads(self._string, _dict=OrderedDict)
        if self._dict is not None:
            self._reformatted = toml.dumps(self._dict)
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
            self._dict = yaml.load(io.StringIO(self._string))
        if self._dict is not None:
            output = io.StringIO()
            yaml.dump(self._dict, output)
            self._reformatted = output.getvalue()

        self._loaded = True
        return True

    @property
    def as_dict(self) -> CommentedMap:
        """On YAML, this dict is a special object with comments and ordered keys."""
        return super().as_dict

    @property
    def as_list(self) -> CommentedSeq:
        """A list of dicts. On YAML, ``as_dict`` might contain a ``list``. This property is just a proxy for typing."""
        return self.as_dict


RoundTripRepresenter.add_representer(SortedDict, RoundTripRepresenter.represent_dict)
