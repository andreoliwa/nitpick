"""CLI tests."""
import pytest

from nitpick.constants import DOT_NITPICK_TOML, PYPROJECT_TOML
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


@pytest.mark.parametrize("config_file", [DOT_NITPICK_TOML, PYPROJECT_TOML])
def test_config_file_already_exists(tmp_path, config_file):
    """Test if .nitpick.toml already exists."""
    project = ProjectMock(tmp_path, pyproject_toml=False, setup_py=True).save_file(config_file, "")
    project.cli_init(f"A config file already exists: {config_file}", exit_code=1)


# FIXME[AA]:
# def test_create_basic_dot_nitpick_toml(tmp_path):
#     """If no config file is found, create a basic .nitpick.toml."""
#     project = ProjectMock(tmp_path, pyproject_toml=False, setup_py=True)
#     project.cli_init()
