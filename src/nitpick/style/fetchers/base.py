"""Base class for fetchers that wrap inner fetchers with caching ability."""
from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from furl import Path, furl
from requests_cache import CachedSession

from nitpick.constants import TOML_EXTENSION


@dataclass(frozen=True)
class StyleFetcher:
    """Base class of all fetchers, it encapsulates get/fetch from a specific source."""

    requires_connection: ClassVar[bool] = False

    # only set when requires_connection is True
    session: CachedSession | None = None
    protocols: tuple[str, ...] = ()
    domains: tuple[str, ...] = ()

    def __post_init__(self):
        """Validate that session has been passed in for requires_connection == True."""
        if self.requires_connection and self.session is None:
            raise ValueError("session is required")

    def preprocess_relative_url(self, url: str) -> str:  # pylint: disable=no-self-use
        """Preprocess a relative URL.

        Only called for urls that lack a scheme (at the very least), being resolved
        against a base URL that matches this specific fetcher.

        """
        return url

    def _normalize_path(self, path: Path) -> Path:  # pylint: disable=no-self-use
        """Normalize the path component of a URL."""
        if path.segments[-1].endswith(TOML_EXTENSION):
            return path
        return Path([*path.segments[:-1], f"{path.segments[-1]}.toml"])

    def _normalize_scheme(self, scheme: str) -> str:  # pylint: disable=no-self-use
        """Normalize the scheme component of a URL."""
        return scheme

    def normalize(self, url: furl) -> furl:
        """Normalize a URL.

        Produces a canonical URL, meant to be used to uniquely identify a style resource.

        - The base name has .toml appended if not already ending in that extension
        - Individual fetchers can further normalize the path and scheme.

        """
        scheme, path = self._normalize_scheme(url.scheme), self._normalize_path(url.path.normalize())
        return url.copy().set(scheme=scheme, path=path)

    def fetch(self, url: furl) -> str:
        """Fetch a style from a specific fetcher."""
        raise NotImplementedError()
