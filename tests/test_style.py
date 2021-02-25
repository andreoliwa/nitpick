"""Style tests."""
# pylint: disable=no-member
from textwrap import dedent
from typing import TYPE_CHECKING
from unittest import mock
from unittest.mock import PropertyMock

import pytest
import responses

from nitpick.constants import DOT_SLASH, PYPROJECT_TOML, READ_THE_DOCS_URL, TOML_EXTENSION
from nitpick.violations import Fuss
from tests.helpers import XFAIL_ON_WINDOWS, ProjectMock, assert_conditions

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize("offline", [False, True])
def test_multiple_styles_overriding_values(offline, tmp_path):
    """Test multiple style files with precedence (the latest ones overrides the previous ones)."""
    ProjectMock(tmp_path).named_style(
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
    ).simulate_run(
        offline=offline, apply=False
    ).assert_errors_contain(
        """
        NIP318 File pyproject.toml has missing values:\x1b[32m
        [tool.black]
        line-length = 100\x1b[0m
        """
    ).assert_errors_contain(
        """
        NIP319 File pyproject.toml has different values. Use this:\x1b[32m
        [tool.black]
        something = 11\x1b[0m
        """
    ).assert_errors_contain(
        """
        NIP321 File setup.cfg was not found. Create it with this content:\x1b[32m
        [flake8]
        inline-quotes = double
        something = 123

        [isort]
        known_first_party = tests
        line_length = 120
        xxx = yyy\x1b[0m
        """
    ).cli_ls(
        """
        pyproject.toml
        setup.cfg
        """
    )


@pytest.mark.parametrize("offline", [False, True])
def test_include_styles_overriding_values(offline, tmp_path):
    """One style file can include another (also recursively). Ignore styles that were already included."""
    ProjectMock(tmp_path).named_style(
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
        include = ["black.toml"]
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
    ).simulate_run(
        offline=offline
    ).assert_errors_contain(
        """
        NIP318 File pyproject.toml has missing values:\x1b[32m
        [tool.black]
        line-length = 100\x1b[0m
        """
    ).assert_errors_contain(
        """
        NIP321 File setup.cfg was not found. Create it with this content:\x1b[32m
        [flake8]
        inline-quotes = double
        something = 123

        [isort]
        known_first_party = tests
        line_length = 120
        xxx = yyy\x1b[0m
        """
    )


@pytest.mark.parametrize("offline", [False, True])
@mock.patch("nitpick.flake8.NitpickFlake8Extension.version", new_callable=PropertyMock(return_value="0.5.3"))
def test_minimum_version(mocked_version, offline, tmp_path):
    """Stamp a style file with a minimum required version, to indicate new features or breaking changes."""
    assert_conditions(mocked_version == "0.5.3")
    ProjectMock(tmp_path).named_style(
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
    ).simulate_run(
        offline=offline
    ).assert_single_error(
        "NIP203 The style file you're using requires nitpick>=1.0 (you have 0.5.3). Please upgrade"
    )


@pytest.mark.parametrize("offline", [False, True])
@XFAIL_ON_WINDOWS
def test_relative_and_other_root_dirs(offline, tmp_path):
    """Test styles in relative and in other root dirs."""
    another_dir: Path = tmp_path / "another_dir"
    project = (
        ProjectMock(tmp_path)
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

    # Use full path on initial styles
    project.pyproject_toml(
        f"""
        [tool.nitpick]
        style = ["{another_dir}/main", "{another_dir}/styles/black"]
        {common_pyproject}
        """
    ).flake8(offline=offline).assert_single_error(
        """
        NIP318 File pyproject.toml has missing values:\x1b[32m
        [tool.black]
        missing = "value"\x1b[0m
        """
    )

    # Reuse the first full path that appears
    project.pyproject_toml(
        f"""
        [tool.nitpick]
        style = ["{another_dir}/main", "styles/black.toml"]
        {common_pyproject}
        """
    ).simulate_run().assert_single_error(
        """
        NIP318 File pyproject.toml has missing values:\x1b[32m
        [tool.black]
        missing = "value"\x1b[0m
        """
    )

    # Allow relative paths
    project.pyproject_toml(
        f"""
        [tool.nitpick]
        style = ["{another_dir}/styles/black", "../poetry"]
        {common_pyproject}
        """
    ).flake8(offline=offline).assert_single_error(
        """
        NIP318 File pyproject.toml has missing values:\x1b[32m
        [tool.black]
        missing = "value"

        [tool.poetry]
        version = "1.0"\x1b[0m
        """
    )


@pytest.mark.parametrize("offline", [False, True])
def test_symlink_subdir(offline, tmp_path):
    """Test relative styles in subdirectories of a symlink dir."""
    target_dir: Path = tmp_path / "target_dir"  # type
    ProjectMock(tmp_path).named_style(
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
        """
        [tool.nitpick]
        style = "symlinked-style"
        """
    ).simulate_run(
        offline=offline
    ).assert_single_error(
        """
        NIP318 File pyproject.toml has missing values:\x1b[32m
        [tool.black]
        line-length = 86\x1b[0m
        """
    )


@responses.activate
def test_relative_style_on_urls(tmp_path):
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
    for filename, body in mapping.items():
        responses.add(responses.GET, f"{base_url}/{filename}.toml", dedent(body), status=200)

    project = ProjectMock(tmp_path)

    common_pyproject = """
        [tool.black]
        line-length = 99
        [tool.pytest]
        some-option = 123
    """
    # Use full path on initial styles
    project.pyproject_toml(
        f"""
        [tool.nitpick]
        style = ["{base_url}/main", "{base_url}/styles/black.toml"]
        {common_pyproject}
        """
    ).simulate_run().assert_single_error(
        """
        NIP318 File pyproject.toml has missing values:\x1b[32m
        [tool.black]
        missing = "value"\x1b[0m
        """
    )

    # Reuse the first full path that appears
    project.pyproject_toml(
        f"""
        [tool.nitpick]
        style = ["{base_url}/main.toml", "styles/black"]
        {common_pyproject}
        """
    ).simulate_run().assert_single_error(
        """
        NIP318 File pyproject.toml has missing values:\x1b[32m
        [tool.black]
        missing = "value"\x1b[0m
        """
    )

    # Allow relative paths
    project.pyproject_toml(
        f"""
        [tool.nitpick]
        style = ["{base_url}/styles/black.toml", "../poetry"]
        {common_pyproject}
        """
    ).simulate_run().assert_single_error(
        """
        NIP318 File pyproject.toml has missing values:\x1b[32m
        [tool.black]
        missing = "value"

        [tool.poetry]
        version = "1.0"\x1b[0m
        """
    )


@responses.activate
@XFAIL_ON_WINDOWS
def test_local_style_should_override_settings(tmp_path):
    """Don't build relative URLs from local file names (starting with "./")."""
    remote_url = "https://example.com/remote-style.toml"
    remote_style = """
        ["pyproject.toml".tool.black]
        line-length = 100
    """
    responses.add(responses.GET, remote_url, dedent(remote_style), status=200)

    local_file = "local-file.toml"
    local_style = """
        ["pyproject.toml".tool.black]
        line-length = 120
    """

    ProjectMock(tmp_path).pyproject_toml(
        f"""
        [tool.nitpick]
        style = [
          "{remote_url}",
          "{DOT_SLASH}{local_file}",
        ]

        [tool.black]
        line-length = 80
        """
    ).named_style(local_file, local_style).api_check().assert_violations(
        Fuss(
            False,
            PYPROJECT_TOML,
            319,
            " has different values. Use this:",
            """
            [tool.black]
            line-length = 120
            """,
        )
    )


@responses.activate
def test_fetch_private_github_urls(tmp_path):
    """Fetch private GitHub URLs with a token on the query string."""
    base_url = "https://raw.githubusercontent.com/user/private_repo/branch/path/to/nitpick-style"
    query_string = "?token=xxx"
    full_private_url = f"{base_url}{TOML_EXTENSION}{query_string}"
    body = """
        ["pyproject.toml".tool.black]
        missing = "thing"
        """
    responses.add(responses.GET, full_private_url, dedent(body), status=200)

    project = ProjectMock(tmp_path).pyproject_toml(
        f"""
        [tool.nitpick]
        style = "{base_url}{query_string}"
        """
    )
    project.flake8(offline=False).assert_single_error(
        """
        NIP318 File pyproject.toml has missing values:\x1b[32m
        [tool.black]
        missing = "thing"\x1b[0m
        """
    )
    project.flake8(offline=True).assert_no_errors()


@pytest.mark.parametrize("offline", [False, True])
def test_merge_styles_into_single_file(offline, tmp_path):
    """Merge all styles into a single TOML file on the cache dir. Also test merging lists (pre-commit repos)."""
    ProjectMock(tmp_path).load_styles("black", "isort").named_style(
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
    ).simulate_run(
        offline=offline
    ).assert_merged_style(
        '''
        ["pyproject.toml".tool.black]
        line-length = 120

        ["setup.cfg".isort]
        line_length = 120
        skip = ".tox,build"
        known_first_party = "tests"

        # The configuration below is needed for compatibility with black.
        # https://github.com/python/black#how-black-wraps-lines
        # https://github.com/PyCQA/isort#multi-line-output-modes
        multi_line_output = 6
        include_trailing_comma = true
        force_grid_wrap = 0
        combine_as_imports = true
        another_key = "some value"

        [[".pre-commit-config.yaml".repos]]
        yaml = """
          - repo: https://github.com/psf/black
            rev: 20.8b1
            hooks:
              - id: black
                args: [--safe, --quiet]
          - repo: https://github.com/asottile/blacken-docs
            rev: v1.9.2
            hooks:
              - id: blacken-docs
                additional_dependencies: [black==20.8b1]
        """

        [[".pre-commit-config.yaml".repos]]
        yaml = """
          - repo: https://github.com/PyCQA/isort
            rev: 5.7.0
            hooks:
              - id: isort
        """
        '''
    )


@pytest.mark.parametrize("offline", [False, True])
def test_invalid_tool_nitpick_on_pyproject_toml(offline, tmp_path):
    """Test invalid [tool.nitpick] on pyproject.toml."""
    project = ProjectMock(tmp_path)
    for style, error_message in [
        (
            'style = [""]\nextra_values = "also raise warnings"',
            "extra_values: Unknown configuration. See https://nitpick.rtfd.io/en/latest/tool_nitpick_section.html."
            + "\nstyle.0: Shorter than minimum length 1.",
        ),
        ('style = ""', "style: Shorter than minimum length 1."),
        ("style = 1", "style: Not a valid string."),
        (
            'style = ["some_file","","   "]',
            "style.1: Shorter than minimum length 1.\nstyle.2: Shorter than minimum length 1.",
        ),
    ]:
        project.pyproject_toml(f"[tool.nitpick]\n{style}").flake8(offline=offline).assert_errors_contain(
            "NIP001 File pyproject.toml has an incorrect style."
            + f" Invalid data in [tool.nitpick]:\x1b[32m\n{error_message}\x1b[0m",
            1,
        )


def test_invalid_toml(tmp_path):
    """Invalid TOML should emit a NIP warning, not raise TomlDecodeError."""
    ProjectMock(tmp_path).style(
        """
        ["setup.cfg".flake8]
        ignore = D100,D104,D202,E203,W503
        """
    ).simulate_run().assert_errors_contain(
        "NIP001 File nitpick-style.toml has an incorrect style. Invalid TOML"
        + " (toml.decoder.TomlDecodeError: This float doesn't have a leading digit (line 2 column 1 char 21))",
        1,
    )


@pytest.mark.parametrize("offline", [False, True])
def test_invalid_nitpick_files(offline, tmp_path):
    """Invalid [nitpick.files] section."""
    ProjectMock(tmp_path).named_style(
        "some_style",
        """
        [xxx]
        wrong = "section"
        """,
    ).named_style(
        "wrong_files",
        """
        [nitpick.files.whatever]
        wrong = "section"
        """,
    ).pyproject_toml(
        """
        [tool.nitpick]
        style = ["some_style", "wrong_files"]
        """
    ).simulate_run(
        offline=offline
    ).assert_errors_contain(
        f"""
        NIP001 File some_style.toml has an incorrect style. Invalid config:\x1b[32m
        xxx: Unknown file. See {READ_THE_DOCS_URL}plugins.html.\x1b[0m
        """
    ).assert_errors_contain(
        f"""
        NIP001 File wrong_files.toml has an incorrect style. Invalid config:\x1b[32m
        nitpick.files.whatever: Unknown file. See {READ_THE_DOCS_URL}nitpick_section.html#nitpick-files.\x1b[0m
        """,
        2,
    )
