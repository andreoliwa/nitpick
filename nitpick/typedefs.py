"""Type definitions."""
from pathlib import Path
from typing import Any, Iterator, List, MutableMapping, Tuple, Type, Union

from ruamel.yaml.comments import CommentedMap, CommentedSeq

PathOrStr = Union[Path, str]
JsonDict = MutableMapping[str, Any]
StrOrList = Union[str, List[str]]
Flake8Error = Tuple[int, int, str, Type]
YieldFlake8Error = Iterator[Flake8Error]
YamlData = Union[CommentedSeq, CommentedMap]
