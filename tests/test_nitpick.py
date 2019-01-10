"""Nitpick tests."""
from flake8_nitpick import ROOT_PYTHON_FILES
from tests.helpers import ProjectMock


def test_no_root_dir():
    """No root dir."""
    assert ProjectMock("no_root", pyproject_toml=False).lint().errors == [
        "NIP101 No root dir found (is this a Python project?)"
    ]


def test_no_main_python_file_root_dir():
    """No main Python file on the root dir."""
    project = ProjectMock("no_main", hello_py=False).touch_file("whatever.sh").lint()
    assert project.errors == [
        "NIP102 None of those Python files was found in the root dir "
        + f"{project.root_dir}: {', '.join(ROOT_PYTHON_FILES)}"
    ]
