"""Support for ``gh`` and ``github`` schemes."""
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Tuple
from urllib.parse import urlparse

from requests import Session, get as requests_get

from nitpick.constants import GIT_AT_REFERENCE
from nitpick.style.fetchers.http import HttpFetcher
from nitpick.typedefs import mypy_property


class GitHubProtocol(Enum):
    """Protocols for the GitHUb scheme."""

    SHORT = "gh"
    LONG = "github"


@dataclass(unsafe_hash=True)
class GitHubURL:
    """Represent a GitHub URL, created from a URL or from its parts."""

    owner: str
    repository: str
    git_reference: str
    path: str

    def __post_init__(self):
        """Remove the initial slash from the path."""
        self._session = Session()
        self.path = self.path.lstrip("/")

    @mypy_property
    @lru_cache()
    def default_branch(self) -> str:
        """Default GitHub branch.

        This property performs a HTTP request and it's memoized with ``lru_cache()``.
        """
        return get_default_branch(self.api_url)

    @property
    def git_reference_or_default(self) -> str:
        """Return the Git reference if informed, or return the default branch."""
        return self.git_reference or str(self.default_branch)

    @property
    def url(self) -> str:
        """Default URL built from attributes."""
        return f"https://github.com/{self.owner}/{self.repository}/blob/{self.git_reference_or_default}/{self.path}"

    @property
    def raw_content_url(self) -> str:
        """Raw content URL for this path."""
        return (
            f"https://raw.githubusercontent.com/{self.owner}/{self.repository}"
            f"/{self.git_reference_or_default}/{self.path}"
        )

    @classmethod
    def parse_url(cls, url: str) -> "GitHubURL":
        """Create an instance by parsing a URL string in any accepted format.

        See the code for ``test_parsing_github_urls()`` for more examples.
        """
        parsed_url = urlparse(url)
        git_reference = ""
        if parsed_url.scheme in GitHubFetcher.protocols:
            owner = parsed_url.netloc
            repo_with_git_reference, path = parsed_url.path.strip("/").split("/", 1)
            if GIT_AT_REFERENCE in repo_with_git_reference:
                repo, git_reference = repo_with_git_reference.split(GIT_AT_REFERENCE)
            else:
                repo = repo_with_git_reference
        else:
            owner, repo, _, git_reference, path = parsed_url.path.strip("/").split("/", 4)
        return cls(owner, repo, git_reference, path)

    @property
    def api_url(self) -> str:
        """API URL for this repo."""
        return f"https://api.github.com/repos/{self.owner}/{self.repository}"

    @property
    def short_protocol_url(self) -> str:
        """Short protocol URL (``gh``)."""
        return self._build_url(GitHubProtocol.SHORT)

    @property
    def long_protocol_url(self) -> str:
        """Long protocol URL (``github``)."""
        return self._build_url(GitHubProtocol.LONG)

    def _build_url(self, protocol: GitHubProtocol):
        if self.git_reference and self.git_reference != self.default_branch:
            at_reference = f"{GIT_AT_REFERENCE}{self.git_reference}"
        else:
            at_reference = ""
        return f"{protocol.value}://{self.owner}/{self.repository}{at_reference}/{self.path}"


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

    protocols: Tuple[str, ...] = (GitHubProtocol.SHORT.value, GitHubProtocol.LONG.value)
    domains: Tuple[str, ...] = ("github.com",)

    def _download(self, url) -> str:
        github_url = GitHubURL.parse_url(url)
        return super()._download(github_url.raw_content_url)
