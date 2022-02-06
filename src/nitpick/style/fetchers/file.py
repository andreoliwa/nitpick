"""Basic local file fetcher."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from nitpick.style.fetchers.base import StyleFetcher


@dataclass(repr=True, unsafe_hash=True)
class FileFetcher(StyleFetcher):  # pylint: disable=too-few-public-methods
    """Fetch a style from a local file."""

    protocols: tuple = ("file", "")

    def _do_fetch(self, url):
        file_path = Path(url).expanduser()
        return file_path.read_text(encoding="UTF-8")
