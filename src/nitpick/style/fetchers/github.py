"""Support for ``gh`` and ``github`` schemes."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import cast

from furl import furl
from requests import Session

from nitpick.constants import GIT_AT_REFERENCE
from nitpick.style.fetchers import Scheme
from nitpick.style.fetchers.http import HttpFetcher

GITHUB_COM = "github.com"
API_GITHUB_COM = "api.github.com"
RAW_GITHUB_COM = "raw.githubusercontent.com"
QUERY_STRING_TOKEN = "token"  # nosec


@dataclass(frozen=True)
class GitHubURL:
    """Represent a GitHub URL, created from a URL or from its parts."""

    owner: str
    repository: str
    git_reference: str
    path: tuple[str, ...] = ()
    auth_token: str | None = None
    query_params: tuple[tuple[str, str], ...] | None = None

    @property
    def default_branch(self) -> str:
        """Default GitHub branch."""
        # get_default_branch() is memoized
        return get_default_branch(self.api_url.url)

    @property
    def credentials(self) -> tuple[str, str] | tuple[()]:
        """Credentials encoded in this URL.

        A tuple of ``(api_token, '')`` if present, or empty tuple otherwise.  If
        the value of ``api_token`` begins with ``$``, it will be replaced with
        the value of the environment corresponding to the remaining part of the
        string.
        """
        token = self.auth_token
        if token is not None and token.startswith("$"):
            token = os.getenv(token[1:])

        return (token, "") if token else ()

    @property
    def git_reference_or_default(self) -> str:
        """Return the Git reference if informed, or return the default branch."""
        return self.git_reference or self.default_branch

    @property
    def url(self) -> furl:
        """Default URL built from attributes."""
        return furl(
            scheme=Scheme.HTTPS,
            host=GITHUB_COM,
            path=[self.owner, self.repository, "blob", self.git_reference_or_default, *self.path],
            query_params=self.query_params,
        )

    @property
    def raw_content_url(self) -> furl:
        """Raw content URL for this path."""
        return furl(
            scheme=Scheme.HTTPS,
            host=RAW_GITHUB_COM,
            path=[self.owner, self.repository, self.git_reference_or_default, *self.path],
            query_params=self.query_params,
        )

    @classmethod
    def from_furl(cls, url: furl) -> GitHubURL:
        """Create an instance from a parsed URL in any accepted format.

        See the code for ``test_parsing_github_urls()`` for more examples.

        """
        auth_token = url.username or url.args.get(QUERY_STRING_TOKEN)
        query_params = tuple((key, value) for key, value in url.args.items() if key != QUERY_STRING_TOKEN)

        if url.scheme in GitHubFetcher.protocols:
            owner = url.host
            repo_with_git_reference, *path = url.path.segments
            repo, _, git_reference = repo_with_git_reference.partition(GIT_AT_REFERENCE)
        else:  # github.com URL (raw.githubusercontent.com is handled by the HTTP fetcher)
            # Skip the 'blob' component in the github.com URL.
            owner, repo, _, git_reference, *path = url.path.segments

        if path and path[-1] == "":
            # strip trailing slashes
            *path, _ = path

        return cls(owner, repo, git_reference, tuple(path), auth_token, query_params)

    @property
    def api_url(self) -> furl:
        """API URL for this repo."""
        return furl(scheme=Scheme.HTTPS, host=API_GITHUB_COM, path=["repos", self.owner, self.repository])

    @property
    def short_protocol_url(self) -> furl:
        """Short protocol URL (``gh``)."""
        return self._build_url(cast(str, Scheme.GH))

    @property
    def long_protocol_url(self) -> furl:
        """Long protocol URL (``github``)."""
        return self._build_url(cast(str, Scheme.GITHUB))

    def _build_url(self, scheme: str) -> furl:
        if self.git_reference and self.git_reference != self.default_branch:
            at_reference = f"{GIT_AT_REFERENCE}{self.git_reference}"
        else:
            at_reference = ""
        return furl(scheme=scheme, host=self.owner, path=[f"{self.repository}{at_reference}", *self.path])


# Dedicated Github API session, to reuse connections.
API_SESSION = Session()


@lru_cache()
def get_default_branch(api_url: str) -> str:
    """Get the default branch from the GitHub repo using the API.

    For now, the request is not authenticated on GitHub, so it might hit a rate limit with:
    ``requests.exceptions.HTTPError: 403 Client Error: rate limit exceeded for url``

    This function is using ``lru_cache()`` as a simple memoizer, trying to avoid this rate limit error.

    Another option for the future: perform an authenticated request to GitHub.
    That would require some user credentials.
    """
    response = API_SESSION.get(api_url)
    response.raise_for_status()

    return response.json()["default_branch"]


@dataclass(frozen=True)
class GitHubFetcher(HttpFetcher):  # pylint: disable=too-few-public-methods
    """Fetch styles from GitHub repositories."""

    protocols: tuple[str, ...] = (Scheme.GH, Scheme.GITHUB)  # type: ignore
    domains: tuple[str, ...] = (GITHUB_COM,)

    @staticmethod
    def _normalize_scheme(scheme: str) -> str:
        # Use github:// instead of gh:// in the canonical URL
        return Scheme.GITHUB if scheme == Scheme.GH else scheme  # type: ignore

    def _download(self, url: furl, **kwargs) -> str:
        github_url = GitHubURL.from_furl(url)
        kwargs.setdefault("auth", github_url.credentials)
        return super()._download(github_url.raw_content_url, **kwargs)
