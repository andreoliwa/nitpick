"""Type definitions."""

from collections.abc import Iterable
from pathlib import Path
from typing import Any

from ruamel.yaml.comments import CommentedMap, CommentedSeq

JsonDict = dict[str, Any]  # https://github.com/python/typing/issues/182#issuecomment-185996450

# keep-sorted start
ElementData = JsonDict | str | int | float | CommentedMap | list[Any]
Flake8Error = tuple[int, int, str, type]
ListOrCommentedSeq = list[Any] | CommentedSeq
PathOrStr = Path | str
StrOrIterable = str | Iterable[str]
StrOrList = str | list[str]
YamlObject = CommentedSeq | CommentedMap
YamlValue = JsonDict | list[Any] | str | float
# keep-sorted end

# Decorated property not supported · Issue #1362 · python/mypy
# https://github.com/python/mypy/issues/1362#issuecomment-562141376
mypy_property: Any = property
