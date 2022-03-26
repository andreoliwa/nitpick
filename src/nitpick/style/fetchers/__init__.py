"""Style fetchers with protocol support."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import auto
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Iterator

from furl import furl
from requests_cache import CachedSession
from strenum import LowercaseStrEnum

from nitpick.enums import CachingEnum
from nitpick.generic import get_scheme
from nitpick.style import parse_cache_option

if TYPE_CHECKING:
    from nitpick.style.fetchers.base import StyleFetcher


class Scheme(LowercaseStrEnum):
    """URL schemes."""

    FILE = auto()
    HTTP = auto()
    HTTPS = auto()
    PY = auto()
    PYPACKAGE = auto()
    GH = auto()
    GITHUB = auto()


@dataclass()
class StyleFetcherManager:
    """Manager that controls which fetcher to be used given a protocol."""

    offline: bool
    cache_dir: Path
    cache_option: str

    session: CachedSession = field(init=False)
    fetchers: dict[str, StyleFetcher] = field(init=False)

    def __post_init__(self):
        """Initialize dependant properties."""
        caching, expire_after = parse_cache_option(self.cache_option)
        # honour caching headers on the response when an expiration time has
        # been set meaning that the server can dictate cache expiration
        # overriding the local expiration time. This may need to become a
        # separate configuration option in future.
        cache_control = caching is CachingEnum.EXPIRES
        self.session = CachedSession(
            str(self.cache_dir / "styles"), expire_after=expire_after, cache_control=cache_control
        )
        self.fetchers = _get_fetchers(self.session)

    def normalize_url(self, url: str | furl, base: furl) -> furl:
        """Normalize a style URL.

        The URL is made absolute against base, then passed to individual fetchers
        to produce a canonical version of the URL.

        """
        # special case: Windows paths can start with a drive letter, which looks
        # like a URL scheme.
        if isinstance(url, str):
            scheme = get_scheme(url)
            if not scheme or len(scheme) == 1:
                url = self._fetcher_for(base).preprocess_relative_url(url)
        absolute = base.copy().join(url)
        return self._fetcher_for(absolute).normalize(absolute)

    def fetch(self, url: furl) -> str | None:
        """Determine which fetcher to be used and fetch from it.

        Returns None when offline is True and the fetcher would otherwise
        require a connection.

        """
        fetcher = self._fetcher_for(url)
        if self.offline and fetcher.requires_connection:
            return None

        return fetcher.fetch(url)

    def _fetcher_for(self, url: furl) -> StyleFetcher:
        """Determine which fetcher to be used.

        Try a fetcher by domain first, then by protocol scheme.

        """
        fetcher = self.fetchers.get(url.host) if url.host else None
        if not fetcher:
            fetcher = self.fetchers.get(url.scheme)
        if not fetcher:
            raise RuntimeError(f"URL protocol {url.scheme!r} is not supported")
        return fetcher


def _get_fetchers(session: CachedSession) -> dict[str, StyleFetcher]:
    # pylint: disable=import-outside-toplevel
    from nitpick.style.fetchers.file import FileFetcher
    from nitpick.style.fetchers.github import GitHubFetcher
    from nitpick.style.fetchers.http import HttpFetcher
    from nitpick.style.fetchers.pypackage import PythonPackageFetcher

    def _factory(klass: type[StyleFetcher]) -> StyleFetcher:
        return klass(session) if klass.requires_connection else klass()

    fetchers = (_factory(FileFetcher), _factory(HttpFetcher), _factory(GitHubFetcher), _factory(PythonPackageFetcher))
    return dict(_fetchers_to_pairs(fetchers))


def _fetchers_to_pairs(fetchers: Iterable[StyleFetcher]) -> Iterator[tuple[str, StyleFetcher]]:
    for fetcher in fetchers:
        for protocol in fetcher.protocols:
            yield protocol, fetcher
        for domain in fetcher.domains:
            yield domain, fetcher
