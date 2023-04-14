"""Base HTTP fetcher, other fetchers can inherit from this to wrap http errors."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import click
import requests
from loguru import logger

from nitpick.enums import OptionEnum
from nitpick.style.fetchers import Scheme
from nitpick.style.fetchers.base import StyleFetcher

if TYPE_CHECKING:
    from furl import furl


@dataclass(frozen=True)
class HttpFetcher(StyleFetcher):
    """Fetch a style from an http/https server."""

    requires_connection = True

    protocols: tuple[str, ...] = (Scheme.HTTP, Scheme.HTTPS)  # type: ignore[has-type]

    def fetch(self, url: furl) -> str:
        """Fetch the style from a web location."""
        try:
            contents = self._download(url)
        except requests.ConnectionError as err:
            logger.exception(f"Request failed with {err}")
            click.secho(
                f"The URL {url} could not be downloaded. Either your network is unreachable or the URL is broken."
                f" Check the URL, fix your connection, or use "
                f" {OptionEnum.OFFLINE.as_flake8_flag()} / {OptionEnum.OFFLINE.as_envvar()}=1",
                fg="red",
                err=True,
            )
            return ""
        return contents

    def _download(self, url: furl, **kwargs) -> str:
        logger.info(f"Downloading style from {url}")
        if self.session is None:
            msg = "No session provided to fetcher"
            raise RuntimeError(msg)
        response = self.session.get(url.url, **kwargs)
        response.raise_for_status()
        return response.text
