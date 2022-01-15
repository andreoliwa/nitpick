"""Type definitions."""
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple, Type, Union

from ruamel.yaml.comments import CommentedMap, CommentedSeq

PathOrStr = Union[Path, str]
JsonDict = Dict[str, Any]  # https://github.com/python/typing/issues/182#issuecomment-185996450
StrOrList = Union[str, List[str]]
StrOrIterable = Union[str, Iterable[str]]
Flake8Error = Tuple[int, int, str, Type]
YamlObject = Union[CommentedSeq, CommentedMap]
YamlValue = Union[JsonDict, List[Any], str, float]
ListOrCommentedSeq = Union[List[Any], CommentedSeq]
ElementData = Union[JsonDict, str, int, float, CommentedMap, List[Any]]

# Decorated property not supported · Issue #1362 · python/mypy
# https://github.com/python/mypy/issues/1362#issuecomment-562141376
mypy_property: Any = property
