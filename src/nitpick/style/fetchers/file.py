"""Basic local file fetcher."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import furl

from nitpick.generic import furl_path_to_python_path
from nitpick.style.fetchers import Scheme
from nitpick.style.fetchers.base import StyleFetcher


@dataclass(frozen=True)
class FileFetcher(StyleFetcher):  # pylint: disable=too-few-public-methods
    """Fetch a style from a local file."""

    protocols: tuple[str, ...] = (Scheme.FILE,)  # type: ignore

    def preprocess_relative_url(self, url: str) -> str:
        """Preprocess a relative URL.

        Only called for urls that lack a scheme (at the very least), being resolved
        against a base URL that matches this specific fetcher.

        Relative paths are file paths; any ~ home reference is expanded at this point.

        """
        # We have to expand ~ values before trying to resolve a path as a file URL
        path = Path(url).expanduser()
        # return absolute paths as URLs as on Windows they could otherwise not resolve
        # cleanly against a file:// base. Relative paths should use POSIX conventions.
        return path.as_uri() if path.is_absolute() else path.as_posix()

    def _normalize_path(self, path: furl.Path) -> furl.Path:
        local_path = furl_path_to_python_path(super()._normalize_path(path))
        return furl.furl(local_path.resolve().as_uri()).path

    def fetch(self, url: furl.furl) -> str:
        """Fetch a style from a local file."""
        return furl_path_to_python_path(url.path).read_text(encoding="UTF-8")
