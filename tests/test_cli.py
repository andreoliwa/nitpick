"""CLI tests."""
import sys

import pytest

from tests.helpers import ProjectMock


@pytest.mark.xfail(condition=sys.platform == "win32", reason="Different path separator on Windows")
def test_simple_error(tmp_path):
    """A simple error on the CLI."""
    project = (
        ProjectMock(tmp_path)
        .style(
            """
        ["pyproject.toml".tool.black]
        line-length = 100
        """
        )
        .pyproject_toml(
            """
        [tool.blabla]
        something = 22
        """
        )
    )

    project.assert_cli_output(
        f"""
        {str(project.root_dir)}/pyproject.toml:1: NIP318  has missing values:
        [tool.black]
        line-length = 100
        """
    )
