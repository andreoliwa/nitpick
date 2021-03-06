"""Config tests."""
import pytest

from tests.helpers import ProjectMock


def test_no_root_dir(request):
    """No root dir."""
    ProjectMock(request, pyproject_toml=False, setup_py=False).create_symlink("hello.py").flake8().assert_single_error(
        "NIP101 No root dir found (is this a Python project?)"
    )


def test_multiple_root_dirs(request):
    """Multiple possible "root dirs" found (e.g.: a requirements.txt file inside a docs dir)."""
    ProjectMock(request, setup_py=False).touch_file("docs/requirements.txt").touch_file("docs/conf.py").pyproject_toml(
        ""
    ).style("").flake8().assert_no_errors()


def test_no_python_file_root_dir(request):
    """No Python file on the root dir."""
    project = ProjectMock(request, setup_py=False).pyproject_toml("").save_file("whatever.sh", "", lint=True).flake8()
    project.assert_single_error(
        "NIP102 No Python file was found on the root dir and subdir of {!r}".format(str(project.root_dir))
    )


@pytest.mark.parametrize(
    "python_file,error", [("depth1.py", False), ("subdir/depth2.py", False), ("subdir/another/depth3.py", True)]
)
def test_at_least_one_python_file(python_file, error, request):
    """At least one Python file on the root dir, even if it's not a main file."""
    project = (
        ProjectMock(request, setup_py=False)
        .style(
            """
            ["pyproject.toml".tool.black]
            lines = 100
            """
        )
        .pyproject_toml(
            """
            [tool.black]
            lines = 100
            """
        )
        .save_file(python_file, "", lint=True)
        .flake8()
    )
    if error:
        project.assert_single_error(
            "NIP102 No Python file was found on the root dir and subdir of {!r}".format(str(project.root_dir))
        )
    else:
        project.assert_no_errors()


def test_django_project_structure(request):
    """Django project with pyproject.toml in the parent dir of manage.py's dir."""
    ProjectMock(request, setup_py=False).pyproject_toml(
        """
        [tool.black]
        lines = 100
        """
    ).setup_cfg(
        """
        [flake8]
        some = thing
        """
    ).touch_file(
        "my_django_project/manage.py"
    ).style(
        """
        ["pyproject.toml".tool.black]
        lines = 100
        ["setup.cfg".flake8]
        some = "thing"
        """
    ).flake8().assert_no_errors()
