"""Config tests."""
import os

import pytest

from nitpick.constants import (
    DOT_NITPICK_TOML,
    GO_MOD,
    GO_SUM,
    MANAGE_PY,
    NITPICK_STYLE_TOML,
    PACKAGE_JSON,
    PRE_COMMIT_CONFIG_YAML,
    PYPROJECT_TOML,
    SETUP_CFG,
    SETUP_PY,
    TOX_INI,
)
from nitpick.core import Nitpick
from nitpick.project import Configuration, find_main_python_file, find_root
from nitpick.violations import ProjectViolations
from tests.helpers import ProjectMock


def test_singleton():
    """Single instance of the Nitpick class; forbid direct instantiation."""
    app1 = Nitpick.singleton()
    app2 = Nitpick.singleton()
    assert app1 is app2

    with pytest.raises(TypeError) as err:
        Nitpick()
    assert "This class cannot be instantiated directly" in str(err)


def test_no_root_dir_with_python_file(tmp_path):
    """No root dir with Python file."""
    project = ProjectMock(tmp_path, pyproject_toml=False, setup_py=False).create_symlink("hello.py")
    error = f"NIP101 {ProjectViolations.NO_ROOT_DIR.message}"
    project.flake8().assert_single_error(error).cli_run(error, exit_code=2).cli_ls(error, exit_code=2)


def test_no_root_dir_no_python_file(tmp_path):
    """No root dir, no Python file."""
    project = ProjectMock(tmp_path, pyproject_toml=False, setup_py=False)
    error = f"NIP101 {ProjectViolations.NO_ROOT_DIR.message}"
    project.cli_run(error, exit_code=2).cli_ls(error, exit_code=2)


def test_multiple_root_dirs(tmp_path):
    """Multiple possible "root dirs" found (e.g.: a requirements.txt file inside a docs dir)."""
    ProjectMock(tmp_path, setup_py=False).touch_file("docs/requirements.txt").touch_file("docs/conf.py").pyproject_toml(
        ""
    ).style("").api_check_then_fix().cli_run()


def test_no_python_file_root_dir(tmp_path):
    """No Python file on the root dir."""
    project = ProjectMock(tmp_path, setup_py=False).pyproject_toml("").save_file("whatever.sh", "", lint=True).flake8()
    project.assert_single_error(
        f"NIP102 No Python file was found on the root dir and subdir of {str(project.root_dir)!r}"
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
        .flake8()
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
        f"""
        ["{PYPROJECT_TOML}".tool.black]
        lines = 100
        ["{SETUP_CFG}".flake8]
        some = "thing"
        """
    ).api_check_then_fix()


def test_no_config_file(tmp_path, caplog):
    """There is a root dir (setup.py), but no config file."""
    project = ProjectMock(tmp_path, pyproject_toml=False, setup_py=True).api_check(offline=True)
    assert project.nitpick_instance.project.read_configuration() == Configuration(None, [], "")
    assert "Config file: none found" in caplog.text


@pytest.mark.parametrize("config_file", [DOT_NITPICK_TOML, PYPROJECT_TOML])
def test_has_one_config_file(tmp_path, config_file, caplog):
    """There is a root dir (setup.py) and a single config file."""
    project = ProjectMock(tmp_path, pyproject_toml=False, setup_py=True)
    project.save_file("local.toml", "").save_file(
        config_file,
        """
        [tool.nitpick]
        style = ["local.toml"]
        cache = "forever"
        """,
    ).api_check(offline=True)
    path = project.root_dir / config_file
    assert project.nitpick_instance.project.read_configuration() == Configuration(path, ["local.toml"], "forever")
    assert f"Config file: reading from {path}" in caplog.text


def test_has_multiple_config_files(tmp_path, caplog):
    """There is a root dir (setup.py) and multiple config files."""
    project = ProjectMock(tmp_path, pyproject_toml=True, setup_py=True)
    project.save_file("local_nit.toml", "").save_file("local_pyproj.toml", "").save_file(
        DOT_NITPICK_TOML,
        """
        [tool.nitpick]
        style = ["local_nit.toml"]
        cache = "never"
        """,
    ).save_file(
        PYPROJECT_TOML,
        """
        [tool.nitpick]
        style = ["local_pyproj.toml"]
        cache = "forever"
        """,
    ).api_check(
        offline=True
    )
    assert project.nitpick_instance.project.read_configuration() == Configuration(
        project.root_dir / DOT_NITPICK_TOML, ["local_nit.toml"], "never"
    )
    assert f"Config file: reading from {project.root_dir / DOT_NITPICK_TOML}" in caplog.text
    assert f"Config file: ignoring existing {project.root_dir / PYPROJECT_TOML}" in caplog.text


@pytest.mark.parametrize(
    "root_file",
    [
        DOT_NITPICK_TOML,
        PRE_COMMIT_CONFIG_YAML,
        PYPROJECT_TOML,
        SETUP_PY,
        SETUP_CFG,
        "requirements.txt",
        "requirements_dev.txt",
        "Pipfile",
        "Pipfile.lock",
        TOX_INI,
        PACKAGE_JSON,
        "Cargo.toml",
        "Cargo.lock",
        GO_MOD,
        GO_SUM,
        NITPICK_STYLE_TOML,
    ],
)
def test_find_root_from_sub_dir(tmp_path, root_file):
    """Find the root dir from a subdir."""
    root = tmp_path / "deep" / "root"
    root.mkdir(parents=True)
    (root / root_file).write_text("")

    curdir = root / "going" / "down" / "the" / "rabbit" / "hole"
    curdir.mkdir(parents=True)
    os.chdir(str(curdir))

    assert find_root(curdir) == root, root_file
    assert find_root(str(curdir)) == root, root_file


def test_find_root_django(tmp_path):
    """Find Django root with manage.py only: the root is where manage.py is."""
    apps_dir = tmp_path / "apps"
    apps_dir.mkdir(parents=True)
    (apps_dir / MANAGE_PY).write_text("")

    assert find_root(apps_dir) == apps_dir

    # Search 2 levels of directories
    assert find_main_python_file(tmp_path) == apps_dir / MANAGE_PY
    assert find_main_python_file(apps_dir) == apps_dir / MANAGE_PY
