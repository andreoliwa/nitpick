"""Type definitions."""
from pathlib import Path
from typing import Any, Dict, List, Tuple, Type, Union

from ruamel.yaml.comments import CommentedMap, CommentedSeq

PathOrStr = Union[Path, str]
JsonDict = Dict[str, Any]
StrOrList = Union[str, List[str]]
Flake8Error = Tuple[int, int, str, Type]
YamlData = Union[CommentedSeq, CommentedMap]

# Decorated property not supported · Issue #1362 · python/mypy
# https://github.com/python/mypy/issues/1362#issuecomment-562141376
mypy_property: Any = property
