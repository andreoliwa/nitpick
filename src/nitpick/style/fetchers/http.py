"""Base HTTP fetcher, other fetchers can inherit from this to wrap http errors."""
from __future__ import annotations

from dataclasses import dataclass

import click
import requests
from loguru import logger

from nitpick.enums import OptionEnum
from nitpick.style.fetchers import Scheme
from nitpick.style.fetchers.base import StyleFetcher


@dataclass(repr=True, unsafe_hash=True)
class HttpFetcher(StyleFetcher):
    """Fetch a style from an http/https server."""

    requires_connection = True

    protocols: tuple[str, ...] = (Scheme.HTTP, Scheme.HTTPS)  # type: ignore

    def _do_fetch(self, url) -> str:
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

    def _download(self, url, **kwargs) -> str:
        logger.info(f"Downloading style from {url}")
        if self.session is None:
            raise RuntimeError("No session provided to fetcher")
        response = self.session.get(url, **kwargs)
        response.raise_for_status()
        return response.text
