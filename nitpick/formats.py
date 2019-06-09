# -*- coding: utf-8 -*-
"""Configuration file formats."""
import abc
from collections import OrderedDict
from pathlib import Path

import toml

from nitpick.typedefs import JsonDict, PathOrStr


class BaseFormat(metaclass=abc.ABCMeta):
    """Base class for configuration file formats."""

    def __init__(self, path: PathOrStr = None, string: str = None, dict_: JsonDict = None) -> None:
        self.path = path
        self._string = string
        self._dict = dict_
        self._reformatted = ""  # type: str
        self._loaded = False

    @abc.abstractmethod
    def load(self):
        """Load the configuration from a file, a string or a dict."""
        pass

    @property
    def as_string(self) -> str:
        """Contents of the file or the original string provided when the instance was created."""
        self.load()
        return self._string or ""

    @property
    def as_dict(self) -> JsonDict:
        """String content converted to a dict."""
        self.load()
        return self._dict or {}

    @property
    def reformatted(self) -> str:
        """Reformat the configuration dict as a new string (it might not match the original string/file contents)."""
        self.load()
        return self._reformatted


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
