"""Support for ``gh`` and ``github`` schemes."""
from dataclasses import dataclass
from enum import Enum
from typing import Tuple
from urllib.parse import urlparse

from nitpick.constants import GIT_AT_REFERENCE
from nitpick.style.fetchers.http import HttpFetcher


class GitHubProtocol(Enum):
    """Protocols for the GitHUb scheme."""

    SHORT = "gh"
    LONG = "github"


@dataclass()
class GitHubURL:
    """Represent a GitHub URL, created from a URL or from its parts."""

    owner: str
    repository: str
    git_reference: str
    path: str

    def __post_init__(self):
        """Remove the initial slash from the path."""
        self.path = self.path.lstrip("/")

    @property
    def url(self) -> str:
        """Default URL built from attributes."""
        return f"https://github.com/{self.owner}/{self.repository}/blob/{self.git_reference}/{self.path}"

    @property
    def raw_content_url(self) -> str:
        """Raw content URL for this path."""
        return f"https://raw.githubusercontent.com/{self.owner}/{self.repository}/{self.git_reference}/{self.path}"

    @classmethod
    def parse_url(cls, url: str) -> "GitHubURL":
        """Create an instance by parsing a URL string."""
        parsed_url = urlparse(url)
        if parsed_url.scheme in GitHubFetcher.protocols:
            owner = parsed_url.netloc
            repo_with_git_reference, path = parsed_url.path.strip("/").split("/", 1)
            if GIT_AT_REFERENCE in repo_with_git_reference:
                repo, git_reference = repo_with_git_reference.split(GIT_AT_REFERENCE)
            else:
                repo = repo_with_git_reference
                git_reference = "develop"
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
        return f"{protocol.value}://{self.owner}/{self.repository}{GIT_AT_REFERENCE}{self.git_reference}/{self.path}"


@dataclass(repr=True, unsafe_hash=True)
class GitHubFetcher(HttpFetcher):  # pylint: disable=too-few-public-methods
    """Fetch styles from GitHub repositories."""

    protocols: Tuple[str, ...] = (GitHubProtocol.SHORT.value, GitHubProtocol.LONG.value)

    def _download(self, url) -> str:
        parsed_url = urlparse(url)
        owner = parsed_url.netloc
        repository = str(parsed_url.path.split("/")[1])

        github_url = GitHubURL(owner, repository, "develop", parsed_url.path.replace(f"/{repository}", ""))
        github_url.git_reference = self.get_default_branch(github_url)

        return super()._download(github_url.raw_content_url)

    def get_default_branch(self, github_url: GitHubURL) -> str:
        """Get the default branch from the GitHub repo using the API."""
        response = self._session.get(github_url.api_url).json()
        return response["default_branch"]
