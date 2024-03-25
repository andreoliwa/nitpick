"""Extensions for the tomlkit package, with drop-in replacement functions and classes.

Eventually, some of the code here should/could be proposed as pull requests to the original package.
"""

from __future__ import annotations

from functools import wraps
from pathlib import Path
from textwrap import dedent
from typing import IO, TYPE_CHECKING, Callable, Iterable

import tomlkit
from tomlkit import TOMLDocument
from tomlkit.exceptions import NonExistentKey
from tomlkit.items import Comment, Key, Table, Whitespace

from nitpick.constants import COMMENT_MARKER_END, COMMENT_MARKER_START

if TYPE_CHECKING:
    from tomlkit.container import Container

# keep-sorted start
TOMLKIT_COMMENT = "# "
TOMLKIT_DOT = "."
# keep-sorted end


def _replace_toml_document_getitem(original_method: Callable) -> Callable:
    """Replace the ::py:meth:`tomlkit.Container.__getitem__` method to allow dotted keys."""

    @wraps(original_method)
    def inner_getitem(self, key: str | Iterable[str]) -> Container | None:
        """If the string key has a dot, recursively get the subkey.

        This is a case that is not handled by tomlkit, it fails with an error.
        """
        if isinstance(key, str) and TOMLKIT_DOT in key:
            current = self
            for subkey in key.split(TOMLKIT_DOT):
                current = current.get(subkey)
                if current is None:
                    raise NonExistentKey(subkey)
            return current
        return original_method(self, key)

    return inner_getitem


TOMLDocument.__getitem__ = _replace_toml_document_getitem(TOMLDocument.__getitem__)


def load(file_pointer: IO[str] | IO[bytes] | Path) -> TOMLDocument:
    """Load a TOML file from a file-like object or path.

    Return an empty document if the file doesn't exist.

    Drop-in replacement for :py:meth:`tomlkit.api.load`.
    """
    if isinstance(file_pointer, Path):
        if not file_pointer.exists():
            return tomlkit.document()
        return tomlkit.loads(file_pointer.read_text(encoding="UTF-8"))
    return tomlkit.load(file_pointer)


def _find_key(container: Container, key: str) -> int | None:
    """Find the index of a key in a container."""
    for index, (pair_key, _) in enumerate(container.body):
        if pair_key and isinstance(pair_key, Key) and pair_key.key == key:
            return index
    return None


def _find_markers_before(container: Container, marker: str, start_index: int) -> tuple[int, int | None, int | None]:
    """Find comment markers before an index; only search comments and whitespace."""
    previous_object_index: int = -1
    marker_start: int | None = None
    marker_end: int | None = None
    current_index = start_index - 1
    while current_index >= 0:
        _, pair_item = container.body[current_index]

        if isinstance(pair_item, Whitespace):
            pass
        elif isinstance(pair_item, Comment):
            stripped = pair_item.trivia.comment.strip(TOMLKIT_COMMENT)
            if stripped.startswith(f"{marker}{COMMENT_MARKER_START}"):
                # If we have multiple (wrong) start markers, continue until the first one
                marker_start = current_index
            elif stripped.startswith(f"{marker}{COMMENT_MARKER_END}") and not marker_end:
                # If we have multiple (wrong) end markers, stop on the last one
                marker_end = current_index
        else:
            previous_object_index = current_index
            break

        current_index -= 1

    return previous_object_index, marker_start, marker_end


def multiline_comment_with_markers(marker: str, text: str) -> list[str]:
    """Add markers to a comment with multiple lines."""
    lines: list[str] = []
    for raw_line in dedent(text).strip().splitlines():
        line = raw_line.lstrip(TOMLKIT_COMMENT)
        if not lines:
            line = f"{marker}{COMMENT_MARKER_START} {line}"
        lines.append(f"{line}")
    lines.append(f"{marker}{COMMENT_MARKER_END}")
    return lines


def update_comment_before(table: Table, key: str, marker: str, comment: str) -> None:
    """Update a comment before a key, between markers.

    Either replace an existing block or create a new one.
    """
    if not comment.strip():
        return

    container: Container = table.value
    key_index = _find_key(container, key)
    hashed_lines = multiline_comment_with_markers(marker, comment)
    new_comment = tomlkit.comment(f"\n{TOMLKIT_COMMENT}".join(hashed_lines))
    if key_index is None:
        table.add(new_comment)
        return

    previous_object_index, marker_start, marker_end = _find_markers_before(container, marker, key_index)
    if marker_end is None:
        marker_end = key_index - 1
    if marker_start is None:
        marker_start = previous_object_index + 1

    # Remove the old comment
    del table.value.body[marker_start : marker_end + 1]
    insert_point = marker_start
    table.value.body.insert(insert_point, (None, new_comment))
