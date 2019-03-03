"""Nitpick tests."""
from flake8_nitpick.constants import ROOT_PYTHON_FILES
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
