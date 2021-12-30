"""Configuration file formats."""
import abc
import json
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable, List, Optional, Type, Union

import dictdiffer
import toml
from autorepr import autorepr
from loguru import logger
from ruamel.yaml import YAML, RoundTripRepresenter, StringIO
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from sortedcontainers import SortedDict

from nitpick.generic import flatten, unflatten
from nitpick.typedefs import JsonDict, PathOrStr, YamlObject


class Comparison:
    """A comparison between two dictionaries, computing missing items and differences."""

    def __init__(
        self,
        actual: Union[JsonDict, YamlObject, "BaseFormat"],
        expected: Union[JsonDict, YamlObject, "BaseFormat"],
        format_class: Type["BaseFormat"],
    ) -> None:
        self.flat_actual = self._normalize_value(actual)
        self.flat_expected = self._normalize_value(expected)

        self.format_class = format_class

        self.missing: Optional[BaseFormat] = None
        self.missing_dict: Union[JsonDict, YamlObject] = {}

        self.diff: Optional[BaseFormat] = None
        self.diff_dict: Union[JsonDict, YamlObject] = {}

    @property
    def has_changes(self) -> bool:
        """Return True is there is a difference or something missing."""
        return bool(self.missing or self.diff)

    @staticmethod
    def _normalize_value(value: Union[JsonDict, YamlObject, "BaseFormat"]) -> JsonDict:
        if isinstance(value, BaseFormat):
            dict_value: JsonDict = value.as_object
        else:
            dict_value = value
        return flatten(dict_value)

    def set_missing(self, missing_dict):
        """Set the missing dict and corresponding format."""
        if not missing_dict:
            return
        self.missing_dict = missing_dict
        if self.format_class:
            self.missing = self.format_class(obj=missing_dict)

    def set_diff(self, diff_dict):
        """Set the diff dict and corresponding format."""
        if not diff_dict:
            return
        self.diff_dict = diff_dict
        if self.format_class:
            self.diff = self.format_class(obj=diff_dict)

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


class BaseFormat(metaclass=abc.ABCMeta):
    """Base class for configuration file formats.

    :param path: Path of the config file to be loaded.
    :param string: Config in string format.
    :param obj: Config object (Python dict, YamlFormat, TomlFormat instances).
    :param ignore_keys: List of keys to ignore when using the comparison methods.
    """

    __repr__ = autorepr(["path"])

    def __init__(
        self,
        *,
        path: PathOrStr = None,
        string: str = None,
        obj: Union[JsonDict, YamlObject, "BaseFormat"] = None,
        ignore_keys: List[str] = None
    ) -> None:
        self.path = path
        self._string = string
        self._object = obj
        if path is None and string is None and obj is None:
            raise RuntimeError("Inform at least one argument: path, string or object")

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
    def as_object(self) -> Union[JsonDict, YamlObject]:
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
        """Cleanup similar values according to the specific format. E.g.: YamlFormat accepts 'True' or 'true'."""
        return list(*args)

    def _create_comparison(self, expected: Union[JsonDict, YamlObject, "BaseFormat"]):
        if not self._ignore_keys:
            return Comparison(self.as_object or {}, expected or {}, self.__class__)

        actual_original: Union[JsonDict, YamlObject] = self.as_object or {}
        actual_copy = actual_original.copy() if isinstance(actual_original, dict) else actual_original

        expected_original: Union[JsonDict, YamlObject, "BaseFormat"] = expected or {}
        if isinstance(expected_original, dict):
            expected_copy = expected_original.copy()
        elif isinstance(expected_original, BaseFormat):
            expected_copy = expected_original.as_object.copy()
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
                    if k in comparison.flat_actual and v != comparison.flat_actual[k]
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


class TomlFormat(BaseFormat):
    """TOML configuration format."""

    def load(self) -> bool:
        """Load a TOML file by its path, a string or a dict."""
        if self._loaded:
            return False
        if self.path is not None:
            self._string = Path(self.path).read_text(encoding="UTF-8")
        if self._string is not None:
            # TODO: I tried to replace toml by tomlkit, but lots of tests break.
            #  The conversion to OrderedDict is not being done recursively (although I'm not sure this is a problem).
            # self._object = OrderedDict(tomlkit.loads(self._string))
            self._object = toml.loads(self._string, _dict=OrderedDict)
        if self._object is not None:
            if isinstance(self._object, BaseFormat):
                self._reformatted = self._object.reformatted
            else:
                # TODO: tomlkit.dumps() renders comments and I didn't find a way to turn this off,
                #  but comments are being lost when the TOML plugin does dict comparisons.
                # self._reformatted = tomlkit.dumps(OrderedDict(self._object), sort_keys=True)
                self._reformatted = toml.dumps(self._object)
        self._loaded = True
        return True


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

    def loads(self, string: str):
        """Load YAML from a string... that unusual use case in a world of files only."""
        return self.load(StringIO(string))

    def dumps(self, data) -> str:
        """Dump to a string... who would want such a thing? One can dump to a file or stdout."""
        output = StringIO()
        self.dump(data, output, transform=None)
        return output.getvalue()


class YamlFormat(BaseFormat):
    """YAML configuration format."""

    document: SensibleYAML

    def load(self) -> bool:
        """Load a YAML file by its path, a string or a dict."""
        if self._loaded:
            return False

        self.document = SensibleYAML()

        if self.path is not None:
            self._string = Path(self.path).read_text(encoding="UTF-8")
        if self._string is not None:
            self._object = self.document.loads(self._string)
        if self._object is not None:
            if isinstance(self._object, BaseFormat):
                self._reformatted = self._object.reformatted
            else:
                self._reformatted = self.document.dumps(self._object)

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


RoundTripRepresenter.add_representer(SortedDict, RoundTripRepresenter.represent_dict)
RoundTripRepresenter.add_representer(OrderedDict, RoundTripRepresenter.represent_dict)


class JsonFormat(BaseFormat):
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
            if isinstance(self._object, BaseFormat):
                self._reformatted = self._object.reformatted
            else:
                # Every file should end with a blank line
                self._reformatted = json.dumps(self._object, sort_keys=True, indent=2) + "\n"
        self._loaded = True
        return True

    @classmethod
    def cleanup(cls, *args: List[Any]) -> List[Any]:
        """Cleanup similar values according to the specific format. E.g.: YamlFormat accepts 'True' or 'true'."""
        return list(args)
