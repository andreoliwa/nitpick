"""Config tests."""
from pathlib import Path
from unittest import mock
from unittest.mock import PropertyMock

from flake8_nitpick.constants import ROOT_PYTHON_FILES
from tests.conftest import TEMP_ROOT_PATH
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


def test_multiple_styles_overriding_values(request):
    """Test multiple style files with precedence (the latest ones overrides the previous ones)."""
    ProjectMock(request).named_style(
        "isort1",
        """
        ["setup.cfg".isort]
        line_length = 80
        known_first_party = "tests"
        xxx = "aaa"
        """,
    ).named_style(
        "styles/isort2",
        """
        ["setup.cfg".isort]
        line_length = 120
        xxx = "yyy"
        """,
    ).named_style(
        "flake8",
        """
        ["setup.cfg".flake8]
        inline-quotes = "double"
        something = 123
        """,
    ).named_style(
        "black",
        """
        ["pyproject.toml".tool.black]
        line-length = 100
        something = 11
        """,
    ).pyproject_toml(
        """
        [tool.nitpick]
        style = ["isort1.toml", "styles/isort2.toml", "flake8.toml", "black.toml"]
        [tool.black]
        something = 22
        """
    ).lint().assert_errors_contain(
        """
        NIP311 File pyproject.toml has missing values. Use this:
        [tool.black]
        line-length = 100
        """
    ).assert_errors_contain(
        """
        NIP312 File pyproject.toml has different values. Use this:
        [tool.black]
        something = 11
        """
    ).assert_errors_contain(
        """
        NIP321 File setup.cfg was not found. Create it with this content:
        [flake8]
        inline-quotes = double
        something = 123

        [isort]
        line_length = 120
        known_first_party = tests
        xxx = yyy
        """
    )


def test_include_styles_overriding_values(request):
    """One style file can include another (also recursively). Ignore styles that were already included."""
    ProjectMock(request).named_style(
        "isort1",
        """
        [nitpick.styles]
        include = "styles/isort2.toml"
        ["setup.cfg".isort]
        line_length = 80
        known_first_party = "tests"
        xxx = "aaa"
        """,
    ).named_style(
        "styles/isort2",
        """
        [nitpick.styles]
        include = ["styles/isort2.toml", "flake8.toml"]
        ["setup.cfg".isort]
        line_length = 120
        xxx = "yyy"
        """,
    ).named_style(
        "flake8",
        """
        [nitpick.styles]
        include = ["black.toml", "", " "]
        ["setup.cfg".flake8]
        inline-quotes = "double"
        something = 123
        """,
    ).named_style(
        "black",
        """
        [nitpick.styles]
        include = ["styles/isort2.toml", "isort1.toml"]
        ["pyproject.toml".tool.black]
        line-length = 100
        """,
    ).pyproject_toml(
        """
            [tool.nitpick]
            style = "isort1.toml"
            """
    ).lint().assert_errors_contain(
        """
        NIP311 File pyproject.toml has missing values. Use this:
        [tool.black]
        line-length = 100
        """
    ).assert_errors_contain(
        """
        NIP321 File setup.cfg was not found. Create it with this content:
        [flake8]
        inline-quotes = double
        something = 123

        [isort]
        line_length = 120
        known_first_party = tests
        xxx = yyy
        """
    )


@mock.patch("flake8_nitpick.plugin.NitpickChecker.version", new_callable=PropertyMock(return_value="0.5.3"))
def test_minimum_version(mocked_version, request):
    """Stamp a style file with a minimum required version, to indicate new features or breaking changes."""
    assert mocked_version == "0.5.3"
    assert (
        ProjectMock(request)
        .named_style(
            "parent",
            """
        [nitpick.styles]
        include = "child.toml"
        ["pyproject.toml".tool.black]
        line-length = 100
        """,
        )
        .named_style(
            "child",
            """
        [nitpick]
        minimum_version = "1.0"
        """,
        )
        .pyproject_toml(
            """
        [tool.nitpick]
        style = "parent.toml"
        [tool.black]
        line-length = 100
        """
        )
        .lint()
        .assert_single_error(
            "NIP203 The style file you're using requires flake8-nitpick>=1.0 (you have 0.5.3). Please upgrade"
        )
    )


def test_relative_and_other_root_dirs(request):
    """Test styles in relative and in other root dirs."""
    another_dir: Path = TEMP_ROOT_PATH / "another_dir"
    project = (
        ProjectMock(request)
        .named_style(
            f"{another_dir}/main",
            """
            [nitpick.styles]
            include = "styles/pytest.toml"
            """,
        )
        .named_style(
            f"{another_dir}/styles/pytest",
            """
            ["pyproject.toml".tool.pytest]
            some-option = 123
            """,
        )
        .named_style(
            f"{another_dir}/styles/black",
            """
            ["pyproject.toml".tool.black]
            line-length = 99
            missing = "value"
            """,
        )
        .named_style(
            f"{another_dir}/poetry",
            """
            ["pyproject.toml".tool.poetry]
            version = "1.0"
            """,
        )
    )

    common_pyproject = """
        [tool.black]
        line-length = 99
        [tool.pytest]
        some-option = 123
    """
    expected_error = """
        NIP311 File pyproject.toml has missing values. Use this:
        [tool.black]
        missing = "value"
    """

    # Use full path on initial styles
    project.pyproject_toml(
        f"""
        [tool.nitpick]
        style = ["{another_dir}/main.toml", "{another_dir}/styles/black.toml"]
        {common_pyproject}
        """
    ).lint().assert_single_error(expected_error)

    # Reuse the first full path that appears
    project.pyproject_toml(
        f"""
        [tool.nitpick]
        style = ["{another_dir}/main.toml", "styles/black.toml"]
        {common_pyproject}
        """
    ).lint().assert_single_error(expected_error)

    # Allow relative paths
    project.pyproject_toml(
        f"""
        [tool.nitpick]
        style = ["{another_dir}/styles/black.toml", "../poetry.toml"]
        {common_pyproject}
        """
    ).lint().assert_single_error(
        f"""
        {expected_error}
        [tool.poetry]
        version = "1.0"
        """
    )


def test_symlink_subdir(request):
    """Test relative styles in subdirectories of a symlink dir."""
    target_dir: Path = TEMP_ROOT_PATH / "target_dir"
    ProjectMock(request).named_style(
        f"{target_dir}/parent",
        """
        [nitpick.styles]
        include = "styles/child.toml"
        """,
    ).named_style(
        f"{target_dir}/styles/child",
        """
        ["pyproject.toml".tool.black]
        line-length = 86
        """,
    ).create_symlink(
        "symlinked-style.toml", target_dir, "parent.toml"
    ).pyproject_toml(
        f"""
        [tool.nitpick]
        style = "symlinked-style.toml"
        """
    ).lint().assert_single_error(
        """
        NIP311 File pyproject.toml has missing values. Use this:
        [tool.black]
        line-length = 86
        """
    )
