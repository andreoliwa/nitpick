"""Nitpick tests."""
from flake8_nitpick import ROOT_PYTHON_FILES, PyProjectTomlChecker
from tests.helpers import ProjectMock


def test_no_root_dir(request):
    """No root dir."""
    assert ProjectMock(request, pyproject_toml=False, setup_py=False).create_symlink_to_fixture(
        "hello.py"
    ).lint().errors == {"NIP101 No root dir found (is this a Python project?)"}


def test_no_main_python_file_root_dir(request):
    """No main Python file on the root dir."""
    project = ProjectMock(request, setup_py=False).save_file("whatever.sh", "", lint=True).lint()
    assert project.errors == {
        "NIP102 None of those Python files was found in the root dir "
        + f"{project.root_dir}: {', '.join(ROOT_PYTHON_FILES)}"
    }


def test_comma_separated_keys_on_style_file(request):
    """Comma separated keys on the style file."""
    project = (
        ProjectMock(request)
        .style(
            """
["setup.cfg"]
comma_separated_values = ["food.eat"]

["setup.cfg".food]
eat = "salt,ham,eggs"
"""
        )
        .setup_cfg(
            """
[food]
eat = spam,eggs,cheese
"""
        )
        .lint()
    )
    project.assert_errors_contain(
        """NIP322 File: setup.cfg: Missing values in key
[food]
eat = ham,salt"""
    )


def test_suggest_poetry_init(request):
    """Suggest poetry init when pyproject.toml does not exist."""
    assert ProjectMock(request, pyproject_toml=False).lint().errors == {
        f"NIP201 {PyProjectTomlChecker.file_name} does not exist. Run 'poetry init' to create one."
    }
