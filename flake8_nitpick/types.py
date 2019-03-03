"""Types."""
from pathlib import Path
from typing import Any, Generator, List, Tuple, Type, Union

PathOrStr = Union[Path, str]
Flake8Error = Tuple[int, int, str, Type]
YieldFlake8Error = Union[List, Generator[Flake8Error, Any, Any]]
