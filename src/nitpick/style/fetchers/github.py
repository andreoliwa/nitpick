"""Support for ``gh`` and ``github`` schemes."""
from dataclasses import dataclass
from typing import Tuple
from urllib.parse import urlparse, uses_netloc, uses_relative

from nitpick.style.fetchers.http import HttpFetcher


@dataclass(repr=True, unsafe_hash=True)
class GitHubFetcher(HttpFetcher):  # pylint: disable=too-few-public-methods
    """Fetch styles from GitHub repositories."""

    _api_url = "https://api.github.com/repos/{owner}/{repository}"
    _download_url = "https://raw.githubusercontent.com/{owner}/{repository}/{git_reference}{path}"
    _registered = False
    protocols: Tuple[str, ...] = ("gh", "github")

    def _post_hooks(self):
        self._register_on_urllib()

    @classmethod
    def _register_on_urllib(cls):
        if cls._registered:
            return

        # This is necessary so urljoin knows how to deal with custom protocols
        for protocol in cls.protocols:
            uses_relative.append(protocol)
            uses_netloc.append(protocol)

    def _download(self, url):
        parsed_url = urlparse(url)
        owner = parsed_url.netloc
        repository = parsed_url.path.split("/")[1]
        main_branch = self._get_main_branch(owner, repository)

        download_url = self._download_url.format(
            owner=owner,
            repository=repository,
            git_reference=main_branch,
            path=parsed_url.path.replace(f"/{repository}", ""),
        )
        return super()._download(download_url)

    def _get_main_branch(self, owner, repository):
        response = self._session.get(self._api_url.format(owner=owner, repository=repository)).json()
        return response["default_branch"]
