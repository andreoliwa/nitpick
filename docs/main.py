"""Macros for MkDocs to generate dynamic content.

This module provides macros for the mkdocs-macros-plugin to generate
version-aware GitHub URLs and other dynamic content.
"""

import os
from subprocess import CalledProcessError, check_output  # nosec


def define_env(env):
    """Define macros, variables, and filters for MkDocs.

    This is the hook function for mkdocs-macros-plugin.
    See: https://mkdocs-macros-plugin.readthedocs.io/
    """

    @env.macro
    def github_url(path: str) -> str:
        """Generate a version-aware GitHub URL for a file in the repository.

        Args:
            path: Relative path to the file from the repository root.
                  Example: "src/nitpick/resources/python/flake8.toml"

        Returns:
            Full GitHub URL pointing to the file at the current git reference.
            Example: "https://github.com/andreoliwa/nitpick/blob/v0.35.0/src/nitpick/resources/python/flake8.toml"

        The git reference is determined in this order:
        1. READTHEDOCS_VERSION environment variable (on ReadTheDocs)
        2. GITHUB_REF_NAME environment variable (on GitHub Actions)
        3. Current git branch/tag from git command
        4. Falls back to "master" if all else fails
        """
        git_ref = _get_git_reference()
        return f"https://github.com/andreoliwa/nitpick/blob/{git_ref}/{path}"

    # Make git_ref available as a variable too
    env.variables["git_ref"] = _get_git_reference()


def _get_git_reference() -> str:
    """Detect the current git reference (branch or tag).

    Returns:
        Git reference string (branch name, tag, or commit SHA).
        Falls back to "master" if detection fails.
    """
    # 1. Check ReadTheDocs environment variable
    # ReadTheDocs sets this to the version being built (e.g., "latest", "stable", "v0.35.0")
    rtd_version = os.getenv("READTHEDOCS_VERSION")
    if rtd_version:
        # Map "latest" to the default branch
        if rtd_version == "latest":
            return "master"
        # Map "stable" to the latest tag (ReadTheDocs handles this)
        # For specific versions like "v0.35.0", use them directly
        return rtd_version

    # 2. Check GitHub Actions environment variable
    # GitHub Actions sets this to the branch or tag name
    github_ref = os.getenv("GITHUB_REF_NAME")
    if github_ref:
        return github_ref

    # 3. Try to get current branch/tag from git
    try:
        # Try to get the current branch name
        result = check_output(["/usr/bin/git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()  # nosec
        # If we're in detached HEAD state, try to get a tag
        if result == "HEAD":
            return check_output(["/usr/bin/git", "describe", "--tags", "--exact-match"], text=True).strip()  # nosec
    except (CalledProcessError, FileNotFoundError):
        # 4. Fall back to master
        return "master"

    return result
