"""Base class for fetchers that wrap inner fetchers with caching ability."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Dict

from requests_cache import CachedSession
from slugify import slugify

from nitpick.generic import is_url
from nitpick.style.fetchers import StyleInfo


@dataclass(repr=True)
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

    def fetch(self, url) -> StyleInfo:
        """Fetch a style from a specific fetcher."""
        contents = self._do_fetch(url)
        if not contents:
            return None, ""
        return self._get_output_path(url), contents

    @staticmethod
    def _get_output_path(url) -> Path:
        if is_url(url):
            return Path(slugify(url))

        return Path(url)

    def _do_fetch(self, url):
        raise NotImplementedError()


FetchersType = Dict[str, "StyleFetcher"]
