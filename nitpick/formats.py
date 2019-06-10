# -*- coding: utf-8 -*-
"""Configuration file formats."""
import abc
from collections import OrderedDict
from pathlib import Path
from typing import Optional, Type

import toml

from nitpick.generic import flatten, unflatten
from nitpick.typedefs import JsonDict, PathOrStr


class Comparison:
    """A comparison between two dictionaries, computing missing items and differences."""

    def __init__(self, format_class: Type["BaseFormat"], actual_dict: JsonDict, expected_dict: JsonDict) -> None:
        self.format_class = format_class  # type: Type["BaseFormat"]
        self.actual = flatten(actual_dict)
        self.expected = flatten(expected_dict)

        self.missing = None  # type: Optional[BaseFormat]
        self.diff = None  # type: Optional[BaseFormat]

    def compare(self) -> "Comparison":
        """Compare two flattened dictionaries and compute missing and different items."""
        if self.expected.items() <= self.actual.items():
            return self

        missing_dict = unflatten({k: v for k, v in self.expected.items() if k not in self.actual})
        if missing_dict:
            self.missing = self.format_class(dict_=missing_dict)

        diff_dict = unflatten(
            {k: v for k, v in self.expected.items() if k in self.actual and self.expected[k] != self.actual[k]}
        )
        if diff_dict:
            self.diff = self.format_class(dict_=diff_dict)

        return self


class BaseFormat(metaclass=abc.ABCMeta):
    """Base class for configuration file formats."""

    def __init__(self, path: PathOrStr = None, string: str = None, dict_: JsonDict = None) -> None:
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

    @classmethod
    def compare(cls, actual: "BaseFormat", expected: "BaseFormat") -> Comparison:
        """Compare two configuration objects."""
        return Comparison(cls, actual.as_dict, expected.as_dict).compare()


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
