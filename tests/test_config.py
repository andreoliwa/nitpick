"""Config tests."""
import pytest

from nitpick.core import Nitpick
from tests.helpers import ProjectMock


def test_singleton():
    """Single instance of the Nitpick class; forbid direct instantiation."""
    app1 = Nitpick.singleton()
    app2 = Nitpick.singleton()
    assert app1 is app2

    with pytest.raises(TypeError) as err:
        Nitpick()
    assert "This class cannot be instantiated directly" in str(err)


def test_no_root_dir(tmp_path):
    """No root dir."""
    ProjectMock(tmp_path, pyproject_toml=False, setup_py=False).create_symlink("hello.py").simulate_run(
        api=False
    ).assert_single_error("NIP101 No root dir found (is this a Python project?)")


def test_multiple_root_dirs(tmp_path):
    """Multiple possible "root dirs" found (e.g.: a requirements.txt file inside a docs dir)."""
    ProjectMock(tmp_path, setup_py=False).touch_file("docs/requirements.txt").touch_file("docs/conf.py").pyproject_toml(
        ""
    ).style("").simulate_run().assert_no_errors().assert_cli_output()


def test_no_python_file_root_dir(tmp_path):
    """No Python file on the root dir."""
    project = (
        ProjectMock(tmp_path, setup_py=False)
        .pyproject_toml("")
        .save_file("whatever.sh", "", lint=True)
        .simulate_run(api=False)
    )
    project.assert_single_error(
        "NIP102 No Python file was found on the root dir and subdir of {!r}".format(str(project.root_dir))
    )


@pytest.mark.parametrize(
    "python_file,error", [("depth1.py", False), ("subdir/depth2.py", False), ("subdir/another/depth3.py", True)]
)
def test_at_least_one_python_file(python_file, error, tmp_path):
    """At least one Python file on the root dir, even if it's not a main file."""
    project = (
        ProjectMock(tmp_path, setup_py=False)
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
        .simulate_run()
    )
    if error:
        project.assert_single_error(
            f"NIP102 No Python file was found on the root dir and subdir of {str(project.root_dir)!r}"
        )
    else:
        project.assert_no_errors()


def test_django_project_structure(tmp_path):
    """Django project with pyproject.toml in the parent dir of manage.py's dir."""
    ProjectMock(tmp_path, setup_py=False).pyproject_toml(
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
    ).simulate_run().assert_no_errors()
