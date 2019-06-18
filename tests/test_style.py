"""Style tests."""
from pathlib import Path
from textwrap import dedent
from unittest import mock
from unittest.mock import PropertyMock

import responses

from nitpick.constants import TOML_EXTENSION
from tests.conftest import TEMP_ROOT_PATH
from tests.helpers import ProjectMock, assert_conditions


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
        style = ["isort1", "styles/isort2", "flake8.toml", "black"]
        [tool.black]
        something = 22
        """
    ).lint().assert_errors_contain(
        """
        NIP318 File pyproject.toml has missing values:
        [tool.black]
        line-length = 100
        """
    ).assert_errors_contain(
        """
        NIP319 File pyproject.toml has different values. Use this:
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
        known_first_party = tests
        line_length = 120
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
        style = "isort1"
        """
    ).lint().assert_errors_contain(
        """
        NIP318 File pyproject.toml has missing values:
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
        known_first_party = tests
        line_length = 120
        xxx = yyy
        """
    )


@mock.patch("nitpick.plugin.NitpickChecker.version", new_callable=PropertyMock(return_value="0.5.3"))
def test_minimum_version(mocked_version, request):
    """Stamp a style file with a minimum required version, to indicate new features or breaking changes."""
    assert_conditions(mocked_version == "0.5.3")
    ProjectMock(request).named_style(
        "parent",
        """
        [nitpick.styles]
        include = "child.toml"
        ["pyproject.toml".tool.black]
        line-length = 100
        """,
    ).named_style(
        "child",
        """
        [nitpick]
        minimum_version = "1.0"
        """,
    ).pyproject_toml(
        """
        [tool.nitpick]
        style = "parent"
        [tool.black]
        line-length = 100
        """
    ).lint().assert_single_error(
        "NIP203 The style file you're using requires nitpick>=1.0 (you have 0.5.3). Please upgrade"
    )


def test_relative_and_other_root_dirs(request):
    """Test styles in relative and in other root dirs."""
    another_dir = TEMP_ROOT_PATH / "another_dir"  # type: Path
    project = (
        ProjectMock(request)
        .named_style(
            "{}/main".format(another_dir),
            """
            [nitpick.styles]
            include = "styles/pytest.toml"
            """,
        )
        .named_style(
            "{}/styles/pytest".format(another_dir),
            """
            ["pyproject.toml".tool.pytest]
            some-option = 123
            """,
        )
        .named_style(
            "{}/styles/black".format(another_dir),
            """
            ["pyproject.toml".tool.black]
            line-length = 99
            missing = "value"
            """,
        )
        .named_style(
            "{}/poetry".format(another_dir),
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
        NIP318 File pyproject.toml has missing values:
        [tool.black]
        missing = "value"
    """

    # Use full path on initial styles
    project.pyproject_toml(
        """
        [tool.nitpick]
        style = ["{another_dir}/main", "{another_dir}/styles/black"]
        {common_pyproject}
        """.format(
            another_dir=another_dir, common_pyproject=common_pyproject
        )
    ).lint().assert_single_error(expected_error)

    # Reuse the first full path that appears
    project.pyproject_toml(
        """
        [tool.nitpick]
        style = ["{}/main", "styles/black.toml"]
        {}
        """.format(
            another_dir, common_pyproject
        )
    ).lint().assert_single_error(expected_error)

    # Allow relative paths
    project.pyproject_toml(
        """
        [tool.nitpick]
        style = ["{}/styles/black", "../poetry"]
        {}
        """.format(
            another_dir, common_pyproject
        )
    ).lint().assert_single_error(
        """
        {}
        [tool.poetry]
        version = "1.0"
        """.format(
            expected_error
        )
    )


def test_symlink_subdir(request):
    """Test relative styles in subdirectories of a symlink dir."""
    target_dir = TEMP_ROOT_PATH / "target_dir"  # type: Path
    ProjectMock(request).named_style(
        "{}/parent".format(target_dir),
        """
        [nitpick.styles]
        include = "styles/child.toml"
        """,
    ).named_style(
        "{}/styles/child".format(target_dir),
        """
        ["pyproject.toml".tool.black]
        line-length = 86
        """,
    ).create_symlink(
        "symlinked-style.toml", target_dir, "parent.toml"
    ).pyproject_toml(
        """
        [tool.nitpick]
        style = "symlinked-style"
        """
    ).lint().assert_single_error(
        """
        NIP318 File pyproject.toml has missing values:
        [tool.black]
        line-length = 86
        """
    )


@responses.activate
def test_relative_style_on_urls(request):
    """Read styles from relative paths on URLs."""
    base_url = "http://www.example.com/sub/folder"
    mapping = {
        "main": """
            [nitpick.styles]
            include = "styles/pytest.toml"
            """,
        "styles/pytest": """
            ["pyproject.toml".tool.pytest]
            some-option = 123
            """,
        "styles/black": """
            ["pyproject.toml".tool.black]
            line-length = 99
            missing = "value"
            """,
        "poetry": """
            ["pyproject.toml".tool.poetry]
            version = "1.0"
            """,
    }
    for file_name, body in mapping.items():
        responses.add(responses.GET, "{}/{}.toml".format(base_url, file_name), dedent(body), status=200)

    project = ProjectMock(request)

    common_pyproject = """
        [tool.black]
        line-length = 99
        [tool.pytest]
        some-option = 123
    """
    expected_error = """
        NIP318 File pyproject.toml has missing values:
        [tool.black]
        missing = "value"
    """

    # Use full path on initial styles
    project.pyproject_toml(
        """
        [tool.nitpick]
        style = ["{base_url}/main", "{base_url}/styles/black.toml"]
        {common_pyproject}
        """.format(
            base_url=base_url, common_pyproject=common_pyproject
        )
    ).lint().assert_single_error(expected_error)

    # Reuse the first full path that appears
    project.pyproject_toml(
        """
        [tool.nitpick]
        style = ["{}/main.toml", "styles/black"]
        {}
        """.format(
            base_url, common_pyproject
        )
    ).lint().assert_single_error(expected_error)

    # Allow relative paths
    project.pyproject_toml(
        """
        [tool.nitpick]
        style = ["{}/styles/black.toml", "../poetry"]
        {}
        """.format(
            base_url, common_pyproject
        )
    ).lint().assert_single_error(
        """
        {}
        [tool.poetry]
        version = "1.0"
        """.format(
            expected_error
        )
    )


@responses.activate
def test_fetch_private_github_urls(request):
    """Fetch private GitHub URLs with a token on the query string."""
    base_url = "https://raw.githubusercontent.com/user/private_repo/branch/path/to/nitpick-style"
    token = "?tokken=xxx"
    full_private_url = "{}{}{}".format(base_url, TOML_EXTENSION, token)
    body = """
        ["pyproject.toml".tool.black]
        missing = "thing"
        """
    responses.add(responses.GET, full_private_url, dedent(body), status=200)

    ProjectMock(request).pyproject_toml(
        """
        [tool.nitpick]
        style = "{}{}"
        """.format(
            base_url, token
        )
    ).lint().assert_single_error(
        """
        NIP318 File pyproject.toml has missing values:
        [tool.black]
        missing = "thing"
    """
    )


def test_merge_styles_into_single_file(request):
    """Merge all styles into a single TOML file on the cache dir. Also test merging lists (pre-commit's repos)."""
    ProjectMock(request).load_styles("black", "isort").named_style(
        "isort_overrides",
        """
        ["setup.cfg".isort]
        another_key = "some value"
        multi_line_output = 6
        """,
    ).pyproject_toml(
        """
        [tool.nitpick]
        style = ["black", "isort", "isort_overrides"]
        """
    ).lint().assert_merged_style(
        '''
        ["pyproject.toml".tool.black]
        line-length = 120

        ["setup.cfg".isort]
        line_length = 120
        skip = ".tox,build"
        known_first_party = "tests"

        # The configuration below is needed for compatibility with black.
        # https://github.com/ambv/black#how-black-wraps-lines
        # https://github.com/timothycrosley/isort#multi-line-output-modes
        multi_line_output = 6
        include_trailing_comma = true
        force_grid_wrap = 0
        combine_as_imports = true
        another_key = "some value"

        [["pre-commit-config.yaml".repos]]
        yaml = """
          - repo: https://github.com/ambv/black
            rev: 19.3b0
            hooks:
              - id: black
                args: [--safe, --quiet]
          - repo: https://github.com/asottile/blacken-docs
            rev: v1.0.0
            hooks:
              - id: blacken-docs
                additional_dependencies: [black==19.3b0]
        """

        [["pre-commit-config.yaml".repos]]
        yaml = """
          - repo: https://github.com/asottile/seed-isort-config
            rev: v1.9.1
            hooks:
              - id: seed-isort-config
          - repo: https://github.com/pre-commit/mirrors-isort
            rev: v4.3.20
            hooks:
              - id: isort
        """
        '''
    )
