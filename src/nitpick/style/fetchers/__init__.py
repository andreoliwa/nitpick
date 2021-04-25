"""Style fetchers with protocol support."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Tuple
from urllib.parse import urlparse

from cachy import CacheManager, Repository
from requests import Session

from nitpick.generic import is_url

if TYPE_CHECKING:
    from nitpick.style.fetchers.base import FetchersType

StyleInfo = Tuple[Optional[Path], str]


# pylint: disable=too-few-public-methods


@dataclass(repr=True)
class StyleFetcherManager:
    """Manager that controls which fetcher to be used given a protocol."""

    offline: bool
    cache_dir: str
    cache_option: str

    cache_repository: Repository = field(init=False)
    fetchers: "FetchersType" = field(init=False)

    def __post_init__(self):
        """Initialize dependant properties."""
        self.cache_repository = CacheManager({"stores": {"file": {"driver": "file", "path": self.cache_dir}}}).store()
        self.fetchers = _get_fetchers(self.cache_repository, self.cache_option)

    def fetch(self, url) -> StyleInfo:
        """Determine which fetcher to be used and fetch from it."""
        scheme = self._get_scheme(url)
        try:
            fetcher = self.fetchers[scheme]
        except KeyError as exc:
            raise RuntimeError(f"protocol {scheme} not supported") from exc

        if self.offline and fetcher.requires_connection:
            return None, ""

        return fetcher.fetch(url)

    @staticmethod
    def _get_scheme(url: str) -> str:
        r"""Get a scheme from an URL or a file.

        >>> StyleFetcherManager._get_scheme("/abc")
        'file'
        >>> StyleFetcherManager._get_scheme("file:///abc")
        'file'
        >>> StyleFetcherManager._get_scheme(r"c:\abc")
        'file'
        >>> StyleFetcherManager._get_scheme("c:/abc")
        'file'
        >>> StyleFetcherManager._get_scheme("http://server.com/abc")
        'http'
        """
        if is_url(url):
            parsed_url = urlparse(url)
            return parsed_url.scheme

        return "file"


def _requests_session() -> Session:
    session = Session()
    return session


def _get_fetchers(cache_repository, cache_option) -> "FetchersType":
    # pylint: disable=import-outside-toplevel
    from nitpick.style.fetchers.file import FileFetcher
    from nitpick.style.fetchers.github import GitHubFetcher
    from nitpick.style.fetchers.http import HttpFetcher

    def _factory(klass):
        return klass(cache_repository, cache_option)

    fetchers = (_factory(FileFetcher), _factory(HttpFetcher), _factory(GitHubFetcher))
    pairs = _fetchers_to_pairs(fetchers)
    return dict(pairs)


def _fetchers_to_pairs(fetchers):
    for fetcher in fetchers:
        for protocol in fetcher.protocols:
            yield protocol, fetcher
