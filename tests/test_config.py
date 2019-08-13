"""Config tests."""
from tests.helpers import ProjectMock


def test_no_root_dir(request):
    """No root dir."""
    ProjectMock(request, pyproject_toml=False, setup_py=False).create_symlink("hello.py").lint().assert_single_error(
        "NIP101 No root dir found (is this a Python project?)"
    )


def test_multiple_root_dirs(request):
    """Multiple possible "root dirs" found (e.g.: a requirements.txt file inside a docs dir)."""
    ProjectMock(request, setup_py=False).touch_file("docs/requirements.txt").touch_file("docs/conf.py").pyproject_toml(
        ""
    ).style("").lint().assert_no_errors()


def test_no_main_python_file_root_dir(request):
    """No main Python file on the root dir."""
    project = ProjectMock(request, setup_py=False).pyproject_toml("").save_file("whatever.sh", "", lint=True).lint()
    project.assert_single_error("NIP102 No Python file was found under the root dir {!r}".format(project.root_dir))


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
    ).lint().assert_no_errors()
