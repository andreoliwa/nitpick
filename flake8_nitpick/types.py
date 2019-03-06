"""Types."""
from pathlib import Path
from typing import Any, Iterator, List, MutableMapping, Tuple, Type, Union

PathOrStr = Union[Path, str]
JsonDict = MutableMapping[str, Any]
StrOrList = Union[str, List[str]]
Flake8Error = Tuple[int, int, str, Type]
YieldFlake8Error = Union[List, Iterator[Flake8Error]]
