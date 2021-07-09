"""Support for ``gh`` and ``github`` schemes."""
from dataclasses import dataclass
from enum import Enum
from typing import Tuple
from urllib.parse import urlparse

from requests import Session

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

    _default_branch = ""

    def __post_init__(self):
        """Remove the initial slash from the path."""
        self._session = Session()
        self.path = self.path.lstrip("/")
        self._default_branch = self.get_default_branch()

    @property
    def git_reference_or_default(self) -> str:
        """Return the Git reference if informed, or return the default branch."""
        return self.git_reference or self._default_branch

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
        """Create an instance by parsing a URL string.

        Accept URLs with this format: ``gh://andreoliwa/nitpick@v0.23.1/src/nitpick/__init__.py``

        The ``@`` syntax is used to get a Git reference (commit, tag, branch).
        It is similar to the syntax used by ``pip`` and ``pipx``:

        - `pip install - VCS Support - Git <https://pip.pypa.io/en/stable/cli/pip_install/?highlight=git#git>`_;
        - `pypa/pipx: Installing from source control <https://github.com/pypa/pipx#installing-from-source-control>`_.

        See the code for ``test_parsing_github_urls()`` for more examples.
        """
        # FIXME[AA]: move this to a .rst
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
        if self.git_reference and self.git_reference != self._default_branch:
            at_reference = f"{GIT_AT_REFERENCE}{self.git_reference}"
        else:
            at_reference = ""
        return f"{protocol.value}://{self.owner}/{self.repository}{at_reference}/{self.path}"

    def get_default_branch(self) -> str:
        """Get the default branch from the GitHub repo using the API."""
        response = self._session.get(self.api_url).json()
        return response["default_branch"]


@dataclass(repr=True, unsafe_hash=True)
class GitHubFetcher(HttpFetcher):  # pylint: disable=too-few-public-methods
    """Fetch styles from GitHub repositories."""

    protocols: Tuple[str, ...] = (GitHubProtocol.SHORT.value, GitHubProtocol.LONG.value)

    def _download(self, url) -> str:
        parsed_url = urlparse(url)
        owner = parsed_url.netloc
        repository = str(parsed_url.path.split("/")[1])

        github_url = GitHubURL(owner, repository, "", parsed_url.path.replace(f"/{repository}", ""))
        return super()._download(github_url.raw_content_url)
