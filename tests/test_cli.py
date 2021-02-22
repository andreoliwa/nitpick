"""CLI tests."""
from tests.helpers import XFAIL_ON_WINDOWS, ProjectMock


@XFAIL_ON_WINDOWS
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

    project.cli_run(
        f"""
        {str(project.root_dir)}/pyproject.toml:1: NIP318  has missing values:
        [tool.black]
        line-length = 100
        """
    )
