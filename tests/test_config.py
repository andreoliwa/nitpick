"""Config tests."""
from unittest import mock
from unittest.mock import PropertyMock

from flake8_nitpick.constants import ROOT_PYTHON_FILES
from tests.helpers import ProjectMock


def test_no_root_dir(request):
    """No root dir."""
    assert ProjectMock(request, pyproject_toml=False, setup_py=False).create_symlink_to_fixture(
        "hello.py"
    ).lint().errors == {"NIP101 No root dir found (is this a Python project?)"}


def test_no_main_python_file_root_dir(request):
    """No main Python file on the root dir."""
    project = ProjectMock(request, setup_py=False).pyproject_toml("").save_file("whatever.sh", "", lint=True).lint()
    assert project.errors == {
        "NIP102 None of those Python files was found in the root dir "
        + f"{project.root_dir}: {', '.join(ROOT_PYTHON_FILES)}"
    }


def test_multiple_styles(request):
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
        "isort2",
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
        style = ["isort1.toml", "isort2.toml", "flake8.toml", "black.toml"]
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


def test_include_styles(request):
    """One style file can include another (also recursively). Ignore styles that were already included."""
    ProjectMock(request).named_style(
        "isort1",
        """
        [nitpick.styles]
        include = "isort2.toml"
        ["setup.cfg".isort]
        line_length = 80
        known_first_party = "tests"
        xxx = "aaa"
        """,
    ).named_style(
        "isort2",
        """
        [nitpick.styles]
        include = ["isort2.toml", "flake8.toml"]
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
        include = ["isort2.toml", "isort1.toml"]
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
        .errors
        == {"NIP203 The style file you're using requires flake8-nitpick>=1.0 (you have 0.5.3). Please upgrade"}
    )
