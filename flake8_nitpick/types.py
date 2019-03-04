"""Types."""
from pathlib import Path
from typing import Any, Dict, Generator, List, Tuple, Type, Union

PathOrStr = Union[Path, str]
TomlDict = Dict[str, Any]
Flake8Error = Tuple[int, int, str, Type]
YieldFlake8Error = Union[List, Generator[Flake8Error, Any, Any]]
