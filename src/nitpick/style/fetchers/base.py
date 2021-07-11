"""Base class for fetchers that wrap inner fetchers with caching ability."""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

from cachy import CacheManager
from loguru import logger
from slugify import slugify

from nitpick.enums import CachingEnum
from nitpick.generic import is_url
from nitpick.style import parse_cache_option
from nitpick.style.fetchers import StyleInfo


@dataclass(repr=True)
class StyleFetcher:
    """Base class of all fetchers, it encapsulate get/fetch from cache."""

    cache_manager: CacheManager
    cache_option: str

    requires_connection = False
    protocols: Tuple[str, ...] = ()
    domains: Tuple[str, ...] = ()

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


FetchersType = Dict[str, "StyleFetcher"]
