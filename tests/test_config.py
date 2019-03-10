"""Config tests."""
from flake8_nitpick.constants import ROOT_PYTHON_FILES
from tests.helpers import ProjectMock


def test_no_root_dir(request):
    """No root dir."""
    ProjectMock(request, pyproject_toml=False, setup_py=False).create_symlink("hello.py").lint().assert_single_error(
        "NIP101 No root dir found (is this a Python project?)"
    )


def test_no_main_python_file_root_dir(request):
    """No main Python file on the root dir."""
    project = ProjectMock(request, setup_py=False).pyproject_toml("").save_file("whatever.sh", "", lint=True).lint()
    project.assert_single_error(
        "NIP102 None of those Python files was found in the root dir "
        + f"{project.root_dir}: {', '.join(ROOT_PYTHON_FILES)}"
    )
