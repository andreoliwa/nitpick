"""Handle import compatibility issues."""

# pylint: skip-file
import sys
from importlib.resources import files  # type: ignore[attr-defined]

try:
    # Python 3.11+ moved Traversable to importlib.resources.abc
    from importlib.resources.abc import Traversable  # type: ignore[attr-defined]
except ImportError:
    # Python 3.9-3.13
    from importlib.abc import Traversable  # type: ignore[no-redef]
