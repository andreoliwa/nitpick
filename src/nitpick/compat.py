"""Handle import compatibility issues."""

# pylint: skip-file
try:
    from importlib.abc import Traversable  # type: ignore[attr-defined]
    from importlib.resources import files  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover
    from importlib_resources import files  # type: ignore[no-redef]
    from importlib_resources.abc import Traversable  # type: ignore[no-redef]
