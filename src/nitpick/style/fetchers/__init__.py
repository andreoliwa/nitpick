"""Style fetchers with protocol support."""
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Tuple
from urllib.parse import urlparse, uses_netloc, uses_relative

from cachy import CacheManager, Repository

from nitpick.generic import is_url

if TYPE_CHECKING:
    from nitpick.style.fetchers.base import FetchersType

StyleInfo = Tuple[Optional[Path], str]


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
        """Determine which fetcher to be used and fetch from it.

        Try a fetcher by domain first, then by protocol scheme.
        """
        domain, scheme = self._get_domain_scheme(url)
        fetcher = None
        if domain:
            fetcher = self.fetchers.get(domain)
        if not fetcher:
            fetcher = self.fetchers.get(scheme)
        if not fetcher:
            raise RuntimeError(f"URI protocol {scheme!r} is not supported")

        if self.offline and fetcher.requires_connection:
            return None, ""

        return fetcher.fetch(url)

    @staticmethod
    def _get_domain_scheme(url: str) -> Tuple[str, str]:
        r"""Get domain and scheme from an URL or a file.

        >>> StyleFetcherManager._get_domain_scheme("/abc")
        ('', 'file')
        >>> StyleFetcherManager._get_domain_scheme("file:///abc")
        ('', 'file')
        >>> StyleFetcherManager._get_domain_scheme(r"c:\abc")
        ('', 'file')
        >>> StyleFetcherManager._get_domain_scheme("c:/abc")
        ('', 'file')
        >>> StyleFetcherManager._get_domain_scheme("http://server.com/abc")
        ('server.com', 'http')
        """
        if is_url(url):
            parsed_url = urlparse(url)
            return parsed_url.netloc, parsed_url.scheme
        return "", "file"


def _get_fetchers(cache_repository, cache_option) -> "FetchersType":
    # pylint: disable=import-outside-toplevel
    from nitpick.style.fetchers.file import FileFetcher
    from nitpick.style.fetchers.github import GitHubFetcher
    from nitpick.style.fetchers.http import HttpFetcher
    from nitpick.style.fetchers.pypackage import PythonPackageFetcher

    def _factory(klass):
        return klass(cache_repository, cache_option)

    fetchers = (_factory(FileFetcher), _factory(HttpFetcher), _factory(GitHubFetcher), _factory(PythonPackageFetcher))
    pairs = _fetchers_to_pairs(fetchers)
    return dict(pairs)


def _fetchers_to_pairs(fetchers):
    for fetcher in fetchers:
        for protocol in fetcher.protocols:
            _register_on_urllib(protocol)
            yield protocol, fetcher
        for domain in fetcher.domains:
            yield domain, fetcher


@lru_cache()
def _register_on_urllib(protocol: str) -> None:
    """Register custom protocols on urllib, only once, if it's not already there.

    This is necessary so urljoin knows how to deal with custom protocols.
    """
    if protocol not in uses_relative:
        uses_relative.append(protocol)

    if protocol not in uses_netloc:
        uses_netloc.append(protocol)
