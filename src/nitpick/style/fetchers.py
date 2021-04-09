"""Style fetchers with protocol support."""
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

import click
import requests
from cachy import CacheManager, Repository
from loguru import logger
from requests import Session
from slugify import slugify

from nitpick.enums import CachingEnum, OptionEnum
from nitpick.generic import is_url
from nitpick.style.cache import parse_cache_option

StyleInfo = Tuple[Optional[Path], str]
FetchersType = Dict[str, "StyleFetcher"]

# pylint: disable=too-few-public-methods


@dataclass(repr=True)
class StyleFetcherManager:
    """Manager that controls which fetcher to be used given a protocol."""

    offline: bool
    cache_dir: str
    cache_option: str

    cache_repository: Repository = field(init=False)
    fetchers: FetchersType = field(init=False)

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


@lru_cache(maxsize=1)
def _requests_session() -> Session:
    session = Session()
    return session


def _get_fetchers(cache_repository, cache_option) -> FetchersType:
    def _factory(klass):
        return klass(cache_repository, cache_option)

    file_fetcher = _factory(FileFetcher)
    http_fetcher = _factory(HttpFetcher)

    return {
        "file": file_fetcher,
        "": file_fetcher,
        "http": http_fetcher,
        "https": http_fetcher,
    }


@dataclass(repr=True)
class StyleFetcher:
    """Base class of all fetchers, it encapsulate get/fetch from cache."""

    cache_manager: CacheManager
    cache_option: str

    requires_connection = False

    def fetch(self, url) -> StyleInfo:
        """Fetch a style form cache or from a specific fetcher."""
        caching, caching_delta = parse_cache_option(self.cache_option)
        path = self._get_output_path(url)
        cached = self._get_from_cache(caching, url)
        if cached:
            return path, cached

        contents = self._do_fetch(url)
        if not contents:
            return None, ""

        self._save_to_cache(caching, caching_delta, url, contents)
        return path, contents

    @staticmethod
    def _get_output_path(url) -> Path:
        if is_url(url):
            return Path(slugify(url))

        return Path(url)

    def _get_from_cache(self, caching, url):
        if caching == CachingEnum.NEVER:
            return None

        cached_value = self.cache_manager.get(url)
        if cached_value is not None:
            logger.debug(f"Using cached value for URL {url}")
            return cached_value

        return None

    def _do_fetch(self, url):
        raise NotImplementedError()

    def _save_to_cache(self, caching, caching_delta, url, contents):
        if caching == CachingEnum.FOREVER:
            logger.debug(f"Caching forever the contents of {url}")
            self.cache_manager.forever(str(url), contents)
        elif caching == CachingEnum.EXPIRES:
            future = datetime.now() + caching_delta
            logger.debug(f"Caching the contents of {url} to expire in {future}")
            self.cache_manager.put(str(url), contents, future)


class HttpFetcher(StyleFetcher):
    """Fetch a style from an http/https server."""

    requires_connection = True

    def _do_fetch(self, url) -> str:
        try:
            contents = self._download(url)
        except requests.ConnectionError as err:
            logger.exception(f"Request failed with {err}")
            click.secho(
                "Your network is unreachable. Fix your connection or use"
                f" {OptionEnum.OFFLINE.as_flake8_flag()} / {OptionEnum.OFFLINE.as_envvar()}=1",
                fg="red",
                err=True,
            )
            return ""
        return contents

    @staticmethod
    def _download(url) -> str:
        response = _requests_session().get(url)
        response.raise_for_status()
        return response.text


class FileFetcher(StyleFetcher):
    """Fetch a style from a local file."""

    def _do_fetch(self, url):
        file_path = Path(url).expanduser()
        return file_path.read_text()
