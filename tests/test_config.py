"""Config tests."""
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
    project = (
        ProjectMock(request)
        .named_style(
            "isort1",
            """
            ["setup.cfg".isort]
            line_length = 80
            known_first_party = "tests"
            xxx = "aaa"
            """,
        )
        .named_style(
            "isort2",
            """
            ["setup.cfg".isort]
            line_length = 120
            xxx = "yyy"
            """,
        )
        .named_style(
            "flake8",
            """
            ["setup.cfg".flake8]
            inline-quotes = "double"
            something = 123
            """,
        )
        .named_style(
            "black",
            """
            ["pyproject.toml".tool.black]
            line-length = 100
            """,
        )
        .pyproject_toml(
            """
            [tool.nitpick]
            style = ["isort1.toml", "isort2.toml", "flake8.toml", "black.toml"]
            """
        )
    )
    project.lint().assert_errors_contain(
        """
        NIP311 File: pyproject.toml: Missing values:
        [tool.black]
        line-length = 100
        """
    ).assert_errors_contain(
        """
        NIP321 File: setup.cfg: Missing file. Suggested content:
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
    project = (
        ProjectMock(request)
        .named_style(
            "isort1",
            """
            [nitpick.styles]
            include = "isort2.toml"
            ["setup.cfg".isort]
            line_length = 80
            known_first_party = "tests"
            xxx = "aaa"
            """,
        )
        .named_style(
            "isort2",
            """
            [nitpick.styles]
            include = ["isort2.toml", "flake8.toml"]
            ["setup.cfg".isort]
            line_length = 120
            xxx = "yyy"
            """,
        )
        .named_style(
            "flake8",
            """
            [nitpick.styles]
            include = ["black.toml", "", " "]
            ["setup.cfg".flake8]
            inline-quotes = "double"
            something = 123
            """,
        )
        .named_style(
            "black",
            """
            [nitpick.styles]
            include = ["isort2.toml", "isort1.toml"]
            ["pyproject.toml".tool.black]
            line-length = 100
            """,
        )
        .pyproject_toml(
            """
            [tool.nitpick]
            style = "isort1.toml"
            """
        )
    )
    project.lint().assert_errors_contain(
        """
        NIP311 File: pyproject.toml: Missing values:
        [tool.black]
        line-length = 100
        """
    ).assert_errors_contain(
        """
        NIP321 File: setup.cfg: Missing file. Suggested content:
        [flake8]
        inline-quotes = double
        something = 123

        [isort]
        line_length = 120
        known_first_party = tests
        xxx = yyy
        """
    )
