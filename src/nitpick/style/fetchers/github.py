"""Support for ``gh`` and ``github`` schemes."""
from __future__ import annotations

import os
from dataclasses import dataclass
from enum import auto
from functools import lru_cache

from furl import furl
from requests import Session, get as requests_get

from nitpick.constants import GIT_AT_REFERENCE, SLASH
from nitpick.style.fetchers import Scheme
from nitpick.style.fetchers.http import HttpFetcher
from nitpick.typedefs import mypy_property

GITHUB_COM = "github.com"
QUERY_STRING_TOKEN = "token"  # nosec


@dataclass(unsafe_hash=True)
class GitHubURL:
    """Represent a GitHub URL, created from a URL or from its parts."""

    owner: str
    repository: str
    git_reference: str
    path: str
    auth_token: str | None = None
    query_string: tuple | None = None

    def __post_init__(self):
        """Remove the initial slash from the path."""
        self._session = Session()
        self.path = self.path.lstrip(SLASH)

    @mypy_property
    @lru_cache()
    def default_branch(self) -> str:
        """Default GitHub branch.

        This property performs a HTTP request and it's memoized with ``lru_cache()``.
        """
        return get_default_branch(self.api_url)

    @property
    def credentials(self) -> tuple:
        """Credentials encoded in this URL.

        A tuple of ``(api_token, '')`` if present, or empty tuple otherwise.  If
        the value of ``api_token`` begins with ``$``, it will be replaced with
        the value of the environment corresponding to the remaining part of the
        string.
        """
        if not self.auth_token:
            return ()

        if self.auth_token.startswith("$"):
            env_token = os.getenv(self.auth_token[1:])

            if env_token:
                return env_token, ""

            return ()

        return self.auth_token, ""

    @property
    def git_reference_or_default(self) -> str:
        """Return the Git reference if informed, or return the default branch."""
        return self.git_reference or str(self.default_branch)

    @property
    def url(self) -> str:
        """Default URL built from attributes."""
        rv = furl(
            scheme=Scheme.HTTPS,
            host=GITHUB_COM,
            path=SLASH.join([self.owner, self.repository, "blob", self.git_reference_or_default, self.path]),
            query_params=dict(self.query_string or {}),
        )
        return str(rv)

    @property
    def raw_content_url(self) -> str:
        """Raw content URL for this path."""
        rv = furl(
            scheme=Scheme.HTTPS,
            host="raw.githubusercontent.com",
            path=SLASH.join([self.owner, self.repository, self.git_reference_or_default, self.path]),
        )
        return str(rv)

    @classmethod
    def parse_url(cls, url: str) -> GitHubURL:
        """Create an instance by parsing a URL string in any accepted format.

        See the code for ``test_parsing_github_urls()`` for more examples.
        """
        parsed_url = furl(url)
        git_reference = ""

        auth_token = parsed_url.username or parsed_url.args.get(QUERY_STRING_TOKEN)

        remaining_query_string = parsed_url.args.copy()
        if QUERY_STRING_TOKEN in remaining_query_string:
            del remaining_query_string[QUERY_STRING_TOKEN]

        if parsed_url.scheme in GitHubFetcher.protocols:
            owner = parsed_url.host or ""
            repo_with_git_reference, path = str(parsed_url.path).strip(SLASH).split(SLASH, 1)
            if GIT_AT_REFERENCE in repo_with_git_reference:
                repo, git_reference = repo_with_git_reference.split(GIT_AT_REFERENCE)
            else:
                repo = repo_with_git_reference
        else:
            # github.com urls have a useless .../blob/... section, but
            # raw.githubusercontent.com doesn't, so take the first 2, then last 2 url
            # components to exclude the blob bit if present.
            owner, repo, *_, git_reference, path = str(parsed_url.path).strip(SLASH).split(SLASH, 4)

        return cls(owner, repo, git_reference, path, auth_token, tuple(remaining_query_string.items()))

    @property
    def api_url(self) -> str:
        """API URL for this repo."""
        rv = furl(
            scheme=Scheme.HTTPS, host=f"api.{GITHUB_COM}", path=SLASH.join(["repos", self.owner, self.repository])
        )
        return str(rv)

    @property
    def short_protocol_url(self) -> str:
        """Short protocol URL (``gh``)."""
        return self._build_url(Scheme.GH)

    @property
    def long_protocol_url(self) -> str:
        """Long protocol URL (``github``)."""
        return self._build_url(Scheme.GITHUB)

    def _build_url(self, scheme: auto):
        if self.git_reference and self.git_reference != self.default_branch:
            at_reference = f"{GIT_AT_REFERENCE}{self.git_reference}"
        else:
            at_reference = ""
        rv = furl(scheme=scheme, host=self.owner, path=SLASH.join([f"{self.repository}{at_reference}", self.path]))
        return str(rv)


@lru_cache()
def get_default_branch(api_url: str) -> str:
    """Get the default branch from the GitHub repo using the API.

    For now, the request is not authenticated on GitHub, so it might hit a rate limit with:
    ``requests.exceptions.HTTPError: 403 Client Error: rate limit exceeded for url``

    This function is using ``lru_cache()`` as a simple memoizer, trying to avoid this rate limit error.

    Another option for the future: perform an authenticated request to GitHub.
    That would require a ``requests.Session`` and some user credentials.
    """
    response = requests_get(api_url)
    response.raise_for_status()

    return response.json()["default_branch"]


@dataclass(repr=True, unsafe_hash=True)
class GitHubFetcher(HttpFetcher):  # pylint: disable=too-few-public-methods
    """Fetch styles from GitHub repositories."""

    protocols: tuple = (Scheme.GH, Scheme.GITHUB)
    domains: tuple[str, ...] = (GITHUB_COM,)

    def _download(self, url, **kwargs) -> str:
        github_url = GitHubURL.parse_url(url)
        if github_url.credentials:
            kwargs.setdefault("auth", github_url.credentials)
        return super()._download(github_url.raw_content_url, **kwargs)
