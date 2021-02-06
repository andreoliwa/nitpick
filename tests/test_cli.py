"""CLI tests."""
from tests.helpers import ProjectMock


def test_simple_error(request):
    """A simple error on the CLI."""
    ProjectMock(request).style(
        """
        ["pyproject.toml".tool.black]
        line-length = 100
        """
    ).pyproject_toml(
        """
        [tool.blabla]
        something = 22
        """
    ).assert_cli_output(
        """
        pyproject.toml:1: NIP318  has missing values:
        [tool.black]
        line-length = 100
        """
    )
