"""Style tests."""
import warnings
from base64 import b64encode
from pathlib import Path
from textwrap import dedent
from unittest import mock
from unittest.mock import PropertyMock

import pytest
import responses
from furl import furl

from nitpick.constants import PYPROJECT_TOML, READ_THE_DOCS_URL, SETUP_CFG, TOML_EXTENSION, TOX_INI
from nitpick.style.fetchers.github import GitHubURL
from nitpick.style.fetchers.pypackage import PythonPackageURL
from nitpick.violations import Fuss
from tests.helpers import SUGGESTION_BEGIN, SUGGESTION_END, ProjectMock, assert_conditions, tomlstring


@pytest.mark.parametrize("offline", [False, True])
def test_multiple_styles_overriding_values(offline, tmp_path):
    """Test multiple style files with precedence (the latest ones overrides the previous ones)."""
    ProjectMock(tmp_path).named_style(
        "isort1",
        f"""
        ["{SETUP_CFG}".isort]
        line_length = 80
        known_first_party = "tests"
        xxx = "aaa"
        """,
    ).named_style(
        "styles/isort2",
        f"""
        ["{SETUP_CFG}".isort]
        line_length = 120
        xxx = "yyy"
        """,
    ).named_style(
        "flake8",
        f"""
        ["{SETUP_CFG}".flake8]
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
    ).flake8(
        offline=offline
    ).assert_errors_contain(
        f"""
        NIP318 File pyproject.toml has missing values:{SUGGESTION_BEGIN}
        [tool.black]
        line-length = 100{SUGGESTION_END}
        """
    ).assert_errors_contain(
        f"""
        NIP319 File pyproject.toml has different values. Use this:{SUGGESTION_BEGIN}
        [tool.black]
        something = 11{SUGGESTION_END}
        """
    ).assert_errors_contain(
        f"""
        NIP321 File {SETUP_CFG} was not found. Create it with this content:{SUGGESTION_BEGIN}
        [flake8]
        inline-quotes = double
        something = 123

        [isort]
        line_length = 120
        known_first_party = tests
        xxx = yyy{SUGGESTION_END}
        """
    ).cli_ls(
        f"""
        {SETUP_CFG}
        {PYPROJECT_TOML}
        """
    )


@pytest.mark.parametrize("offline", [False, True])
def test_include_styles_overriding_values(offline, tmp_path):
    """One style file can include another (also recursively). Ignore styles that were already included."""
    ProjectMock(tmp_path).named_style(
        "isort1",
        f"""
        [nitpick.styles]
        include = "styles/isort2.toml"
        ["{SETUP_CFG}".isort]
        line_length = 80
        known_first_party = "tests"
        xxx = "aaa"
        """,
    ).named_style(
        "styles/isort2",
        f"""
        [nitpick.styles]
        include = ["./isort2.toml", "../flake8.toml"]
        ["{SETUP_CFG}".isort]
        line_length = 120
        xxx = "yyy"
        """,
    ).named_style(
        "flake8",
        f"""
        [nitpick.styles]
        include = ["black.toml"]
        ["{SETUP_CFG}".flake8]
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
    ).flake8(
        offline=offline
    ).assert_errors_contain(
        f"""
        NIP318 File pyproject.toml has missing values:{SUGGESTION_BEGIN}
        [tool.black]
        line-length = 100{SUGGESTION_END}
        """
    ).assert_errors_contain(
        f"""
        NIP321 File {SETUP_CFG} was not found. Create it with this content:{SUGGESTION_BEGIN}
        [flake8]
        inline-quotes = double
        something = 123

        [isort]
        line_length = 120
        known_first_party = tests
        xxx = yyy{SUGGESTION_END}
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
    ).flake8(
        offline=offline
    ).assert_single_error(
        "NIP203 The style file you're using requires nitpick>=1.0 (you have 0.5.3). Please upgrade"
    )


@pytest.mark.parametrize("offline", [False, True])
def test_relative_and_other_root_dirs(offline, tmp_path):
    """Test styles in relative and in other root dirs."""
    another_dir: Path = tmp_path / "another_dir"
    project = (
        ProjectMock(tmp_path)
        .named_style(
            another_dir / "main",
            """
            [nitpick.styles]
            include = "styles/pytest.toml"
            """,
        )
        .named_style(
            another_dir / "styles/pytest",
            """
            ["pyproject.toml".tool.pytest]
            some-option = 123
            """,
        )
        .named_style(
            another_dir / "styles/black",
            """
            ["pyproject.toml".tool.black]
            line-length = 99
            missing = "value"
            """,
        )
        .named_style(
            another_dir / "poetry",
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
        style = [{tomlstring(another_dir / "main")}, {tomlstring(another_dir / "styles/black")}]
        {common_pyproject}
        """
    ).flake8(offline=offline).assert_single_error(
        f"""
        NIP318 File pyproject.toml has missing values:{SUGGESTION_BEGIN}
        [tool.black]
        missing = "value"{SUGGESTION_END}
        """
    )

    # Allow relative paths
    project.pyproject_toml(
        f"""
        [tool.nitpick]
        style = [{tomlstring(another_dir / "styles/black")}, "./another_dir/poetry"]
        {common_pyproject}
        """
    ).flake8(offline=offline).assert_single_error(
        f"""
        NIP318 File pyproject.toml has missing values:{SUGGESTION_BEGIN}
        [tool.black]
        missing = "value"

        [tool.poetry]
        version = "1.0"{SUGGESTION_END}
        """
    )


@pytest.mark.parametrize("offline", [False, True])
def test_symlink_subdir(offline, tmp_path):
    """Test relative styles in subdirectories of a symlink dir."""
    target_dir: Path = tmp_path / "target_dir"
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
    ).flake8(
        offline=offline
    ).assert_single_error(
        f"""
        NIP318 File pyproject.toml has missing values:{SUGGESTION_BEGIN}
        [tool.black]
        line-length = 86{SUGGESTION_END}
        """
    )


@responses.activate
def test_relative_style_on_urls(tmp_path):
    """Read styles from relative paths on URLs."""
    base_url = "http://www.example.com/sub/folder"
    mapping = {
        "main": """
            [nitpick.styles]
            include = "presets/python.toml"
            """,
        "presets/python": """
            [nitpick.styles]
            include = [
                "../styles/pytest.toml",
                "../styles/black.toml",
            ]
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
        style = ["{base_url}/main"]
        {common_pyproject}
        """
    ).api_check().assert_violations(
        Fuss(
            False,
            PYPROJECT_TOML,
            318,
            " has missing values:",
            """
            [tool.black]
            missing = "value"
            """,
        )
    )


@responses.activate
def test_local_style_should_override_settings(tmp_path):
    """Don't build relative URLs from local file names (starting with "./")."""
    remote_url = "https://example.com/remote-style.toml"
    remote_style = """
        ["pyproject.toml".tool.black]
        line-length = 100
    """
    responses.add(responses.GET, remote_url, dedent(remote_style), status=200)

    local_file = "./local-file.toml"
    local_style = """
        ["pyproject.toml".tool.black]
        line-length = 120
    """

    ProjectMock(tmp_path).pyproject_toml(
        f"""
        [tool.nitpick]
        style = [
          "{remote_url}",
          "{local_file}",
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
    gh_url = "https://github.com/user/private_repo/blob/branch/path/to/nitpick-style"
    file_token = "query-string-token-generated-by-github-for-private-files"
    full_raw_url = f"https://raw.githubusercontent.com/user/private_repo/branch/path/to/nitpick-style{TOML_EXTENSION}"
    body = """
        ["pyproject.toml".tool.black]
        missing = "thing"
    """
    responses.add(responses.GET, full_raw_url, dedent(body), status=200)

    project = ProjectMock(tmp_path).pyproject_toml(
        f"""
        [tool.nitpick]
        style = "{gh_url}?token={file_token}"
        """
    )
    project.flake8(offline=False).assert_single_error(
        f"""
        NIP318 File pyproject.toml has missing values:{SUGGESTION_BEGIN}
        [tool.black]
        missing = "thing"{SUGGESTION_END}
        """
    )
    token_on_basic_auth = b64encode(f"{file_token}:".encode()).decode().strip()
    assert responses.calls[0].request.headers["Authorization"] == f"Basic {token_on_basic_auth}"
    project.flake8(offline=True).assert_no_errors()


@pytest.mark.parametrize(
    "style_url",
    [
        # Without commit reference (uses default branch)
        "github://andreoliwa/nitpick/initial.toml",
        "gh://andreoliwa/nitpick/initial.toml",
        # Explicit commit reference
        "github://andreoliwa/nitpick@develop/initial.toml",
        "gh://andreoliwa/nitpick@develop/initial.toml",
        # Regular GitHub URL
        "https://github.com/andreoliwa/nitpick/blob/develop/initial.toml",
    ],
)
def test_github_url_without_token_has_no_credentials(style_url):
    """Check private GitHub URLs with a token in various places are parsed correctly."""
    parsed = GitHubURL.from_furl(furl(style_url))
    assert parsed.credentials == ()


@pytest.mark.parametrize(
    "url",
    [
        # Without commit reference (uses default branch)
        "github://token@andreoliwa/nitpick/initial.toml",
        "gh://token@andreoliwa/nitpick/initial.toml",
        # Explicit commit reference
        "github://token@andreoliwa/nitpick@develop/initial.toml",
        "gh://token@andreoliwa/nitpick@develop/initial.toml",
        # Regular GitHub URL
        "https://token@github.com/andreoliwa/nitpick/blob/develop/initial.toml",
        # Raw URL directly
        "https://token@raw.githubusercontent.com/andreoliwa/nitpick/develop/initial.toml",
    ],
)
def test_github_url_with_fixed_userinfo_token_has_correct_credential(url):
    """Check private GitHub URLs with a token in various places are parsed correctly."""
    parsed = GitHubURL.from_furl(furl(url))
    assert parsed.credentials == ("token", "")


@pytest.mark.parametrize(
    "url",
    [
        # Without commit reference (uses default branch)
        "github://$TOKEN@andreoliwa/nitpick/initial.toml",
        "gh://$TOKEN@andreoliwa/nitpick/initial.toml",
        # Explicit commit reference
        "github://$TOKEN@andreoliwa/nitpick@develop/initial.toml",
        "gh://$TOKEN@andreoliwa/nitpick@develop/initial.toml",
        # Regular GitHub URL
        "https://$TOKEN@github.com/andreoliwa/nitpick/blob/develop/initial.toml",
        # Raw URL directly
        "https://$TOKEN@raw.githubusercontent.com/andreoliwa/nitpick/develop/initial.toml",
    ],
)
def test_github_url_with_variable_userinfo_token_has_correct_credential(url, monkeypatch):
    """Check private GitHub URLs with a token in various places are parsed correctly."""
    monkeypatch.setenv("TOKEN", "envvar-token")
    parsed = GitHubURL.from_furl(furl(url))
    assert parsed.credentials == ("envvar-token", "")


@pytest.mark.parametrize(
    "url",
    [
        # Without commit reference (uses default branch)
        "github://andreoliwa/nitpick/initial.toml?token=$ENVVAR",
        "gh://andreoliwa/nitpick/initial.toml?token=$ENVVAR",
        # Explicit commit reference
        "github://andreoliwa/nitpick@develop/initial.toml?token=$ENVVAR",
        "gh://andreoliwa/nitpick@develop/initial.toml?token=$ENVVAR",
        # Regular GitHub URL
        "https://github.com/andreoliwa/nitpick/blob/develop/initial.toml?token=$ENVVAR",
        # Raw URL directly
        "https://raw.githubusercontent.com/andreoliwa/nitpick/develop/initial.toml?token=$ENVVAR",
        # token in both userinfo and queryargs uses userinfo one
        "github://$ENVVAR@andreoliwa/nitpick/initial.toml?token=$NOTUSED",
    ],
)
def test_github_url_with_variable_query_token_has_correct_credential(url, monkeypatch):
    """Check private GitHub URLs with a token in various places are parsed correctly."""
    monkeypatch.setenv("ENVVAR", "envvar-token")
    parsed = GitHubURL.from_furl(furl(url))
    assert parsed.credentials == ("envvar-token", "")


def test_github_url_with_missing_envvar_has_empty_credential(monkeypatch):
    """Environment var that doesn't exist is replaced with empty string."""
    monkeypatch.delenv("MISSINGVAR", raising=False)
    parsed = GitHubURL.from_furl(furl("https://github.com/foo/bar/blob/branch/filename.toml?token=$MISSINGVAR"))
    assert parsed.credentials == ()


def test_github_url_query_token_retains_other_queryparams(monkeypatch):
    """Querystring isn't modified by the token switcharoo."""
    parsed = GitHubURL.from_furl(furl("https://github.com/foo/bar/blob/branch/filename.toml?leavemealone=ok"))
    assert ("leavemealone", "ok") in parsed.url.query.params.items()
    parsed = GitHubURL.from_furl(
        furl("https://github.com/foo/bar/blob/branch/filename.toml?token=somevar&leavemealone=ok")
    )
    assert parsed.credentials == ("somevar", "")
    assert ("leavemealone", "ok") in parsed.url.query.params.items()


@responses.activate
def test_include_remote_style_from_local_style(tmp_path):
    """Test include of remote style when there is only a local style."""
    remote_style = "https://raw.githubusercontent.com/user/repo/branch/path/to/nitpick-style"
    url_with_extension = f"{remote_style}{TOML_EXTENSION}"
    body = """
        ["tox.ini".section]
        key = "value"
    """
    responses.add(responses.GET, url_with_extension, dedent(body), status=200)

    project = ProjectMock(tmp_path).style(
        f"""
        [nitpick.styles]
        include = [
            "{remote_style}"
        ]
        """
    )
    project.assert_file_contents(TOX_INI, None).api_check_then_fix(
        Fuss(True, TOX_INI, 321, " was not found. Create it with this content:", "[section]\nkey = value")
    ).assert_file_contents(
        TOX_INI,
        """
        [section]
        key = value
        """,
        PYPROJECT_TOML,
        None,
    )


@pytest.mark.parametrize("offline", [False, True])
def test_merge_styles_into_single_file(offline, tmp_path):
    """Merge all styles into a single TOML file on the cache dir. Also test merging lists (pre-commit repos)."""
    warnings.simplefilter("ignore")  # "repos.yaml" key
    ProjectMock(tmp_path).named_style(
        "black",
        '''
        ["pyproject.toml".tool.black]
        line-length = 120

        [[".pre-commit-config.yaml".repos]]
        yaml = """
          - repo: https://github.com/psf/black
            rev: 21.5b2
            hooks:
              - id: black
                args: [--safe, --quiet]
          - repo: https://github.com/asottile/blacken-docs
            rev: v1.10.0
            hooks:
              - id: blacken-docs
                additional_dependencies: [black==21.5b2]
        """
        ''',
    ).named_style(
        "isort",
        '''
        ["setup.cfg".isort]
        line_length = 120
        skip = ".tox,build"
        known_first_party = "tests"

        # The configuration below is needed for compatibility with black.
        # https://github.com/python/black#how-black-wraps-lines
        # https://github.com/PyCQA/isort#multi-line-output-modes
        multi_line_output = 3
        include_trailing_comma = true
        force_grid_wrap = 0
        combine_as_imports = true

        [[".pre-commit-config.yaml".repos]]
        yaml = """
          - repo: https://github.com/PyCQA/isort
            rev: 5.8.0
            hooks:
              - id: isort
        """
        ''',
    ).named_style(
        "isort_overrides",
        f"""
        ["{SETUP_CFG}".isort]
        another_key = "some value"
        multi_line_output = 6
        """,
    ).pyproject_toml(
        """
        [tool.nitpick]
        style = ["black", "isort", "isort_overrides"]
        """
    ).flake8(
        offline=offline
    ).assert_merged_style(
        f'''
        ["pyproject.toml".tool.black]
        line-length = 120

        ["{SETUP_CFG}".isort]
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
            rev: 21.5b2
            hooks:
              - id: black
                args: [--safe, --quiet]
          - repo: https://github.com/asottile/blacken-docs
            rev: v1.10.0
            hooks:
              - id: blacken-docs
                additional_dependencies: [black==21.5b2]
        """

        [[".pre-commit-config.yaml".repos]]
        yaml = """
          - repo: https://github.com/PyCQA/isort
            rev: 5.8.0
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
            f"extra_values: Unknown configuration. See {READ_THE_DOCS_URL}configuration.html."
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
            + f" Invalid data in [tool.nitpick]:{SUGGESTION_BEGIN}\n{error_message}{SUGGESTION_END}",
            1,
        )


def test_invalid_toml(tmp_path):
    """Invalid TOML should emit a NIP warning, not raise TomlDecodeError."""
    ProjectMock(tmp_path).style(
        f"""
        ["{SETUP_CFG}".flake8]
        ignore = D100,D104,D202,E203,W503
        """
    ).api_check_then_fix(
        Fuss(
            False,
            "nitpick-style.toml",
            1,
            " has an incorrect style. Invalid TOML"
            " (toml.decoder.TomlDecodeError: This float doesn't have a leading digit (line 2 column 1 char 21))",
        )
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
    ).flake8(
        offline=offline
    ).assert_errors_contain(
        f"""
        NIP001 File some_style.toml has an incorrect style. Invalid config:{SUGGESTION_BEGIN}
        xxx: Unknown file. See {READ_THE_DOCS_URL}plugins.html.{SUGGESTION_END}
        """
    ).assert_errors_contain(
        f"""
        NIP001 File wrong_files.toml has an incorrect style. Invalid config:{SUGGESTION_BEGIN}
        nitpick.files.whatever: Unknown file. See {READ_THE_DOCS_URL}nitpick_section.html#nitpick-files.{SUGGESTION_END}
        """,
        2,
    )


@responses.activate
@pytest.mark.parametrize(
    "style_url",
    [
        # Without commit reference (uses default branch)
        "github://andreoliwa/nitpick/initial.toml",
        "gh://andreoliwa/nitpick/initial.toml",
        # Explicit commit reference
        "github://andreoliwa/nitpick@develop/initial.toml",
        "gh://andreoliwa/nitpick@develop/initial.toml",
        # Regular GitHub URL
        "https://github.com/andreoliwa/nitpick/blob/develop/initial.toml",
        # Raw URL directly
        "https://raw.githubusercontent.com/andreoliwa/nitpick/develop/initial.toml",
    ],
)
def test_always_fetch_github_raw_url(style_url, tmp_path):
    """Test that gh://, github:// and normal github URLs can be fetched always by their corresponding raw URL."""
    raw_url = "https://raw.githubusercontent.com/andreoliwa/nitpick/develop"
    data = [
        (
            f"{raw_url}/initial.toml",
            """
            [nitpick.styles]
            include = "black.toml"
            """,
        ),
        (
            f"{raw_url}/black.toml",
            """
            ["pyproject.toml".tool.black]
            line-length = 120
            """,
        ),
    ]
    for url, style in data:
        responses.add(responses.GET, url, dedent(style), status=200)

    responses.add(responses.GET, "https://api.github.com/repos/andreoliwa/nitpick", '{"default_branch": "develop"}')

    ProjectMock(tmp_path).pyproject_toml(
        f"""
        [tool.nitpick]
        style = ["{style_url}"]
        """
    ).api_check().assert_violations(
        Fuss(
            False,
            PYPROJECT_TOML,
            318,
            " has missing values:",
            """
            [tool.black]
            line-length = 120
            """,
        )
    )


@responses.activate
@pytest.mark.parametrize(
    "original_url, expected_url, git_reference, raw_git_reference, at_reference",
    [
        (
            "https://github.com/andreoliwa/nitpick/blob/develop/src/nitpick/__init__.py",
            "https://github.com/andreoliwa/nitpick/blob/develop/src/nitpick/__init__.py",
            "develop",
            "develop",
            "",
        ),
        (
            "gh://andreoliwa/nitpick/src/nitpick/__init__.py",
            "https://github.com/andreoliwa/nitpick/blob/develop/src/nitpick/__init__.py",
            "",
            "develop",
            "",
        ),
        (
            "github://andreoliwa/nitpick/src/nitpick/__init__.py",
            "https://github.com/andreoliwa/nitpick/blob/develop/src/nitpick/__init__.py",
            "",
            "develop",
            "",
        ),
        (
            "https://github.com/andreoliwa/nitpick/blob/v0.26.0/src/nitpick/__init__.py",
            "https://github.com/andreoliwa/nitpick/blob/v0.26.0/src/nitpick/__init__.py",
            "v0.26.0",
            "v0.26.0",
            "@v0.26.0",
        ),
        (
            "gh://andreoliwa/nitpick@v0.23.1/src/nitpick/__init__.py",
            "https://github.com/andreoliwa/nitpick/blob/v0.23.1/src/nitpick/__init__.py",
            "v0.23.1",
            "v0.23.1",
            "@v0.23.1",
        ),
        (
            "github://andreoliwa/nitpick@master/src/nitpick/__init__.py",
            "https://github.com/andreoliwa/nitpick/blob/master/src/nitpick/__init__.py",
            "master",
            "master",
            "@master",
        ),
    ],
)
def test_parsing_github_urls(original_url, expected_url, git_reference, raw_git_reference, at_reference):
    """Test a GitHub URL and its parts, raw URL, API URL."""
    responses.add(responses.GET, "https://api.github.com/repos/andreoliwa/nitpick", '{"default_branch": "develop"}')

    gh = GitHubURL.from_furl(furl(original_url))
    assert gh.owner == "andreoliwa"
    assert gh.repository == "nitpick"
    assert gh.git_reference == git_reference
    assert gh.path == ("src", "nitpick", "__init__.py")
    assert gh.raw_content_url == furl(
        f"https://raw.githubusercontent.com/andreoliwa/nitpick/{raw_git_reference}/src/nitpick/__init__.py"
    )
    assert gh.url == furl(expected_url)
    assert gh.api_url == furl("https://api.github.com/repos/andreoliwa/nitpick")
    assert gh.short_protocol_url == furl(f"gh://andreoliwa/nitpick{at_reference}/src/nitpick/__init__.py")
    assert gh.long_protocol_url == furl(f"github://andreoliwa/nitpick{at_reference}/src/nitpick/__init__.py")


@pytest.mark.parametrize(
    "original_url, import_path, resource_name",
    [
        ("py://nitpick/styles/nitpick-style.toml", "nitpick.styles", "nitpick-style.toml"),
        ("py://some_package/nitpick.toml", "some_package", "nitpick.toml"),
        ("pypackage://nitpick/styles/nitpick-style.toml", "nitpick.styles", "nitpick-style.toml"),
        ("pypackage://some_package/nitpick.toml", "some_package", "nitpick.toml"),
    ],
)
def test_parsing_python_package_urls(original_url, import_path, resource_name):
    """Test a resource URL of python package and its parts."""
    pp = PythonPackageURL.from_furl(furl(original_url))
    assert pp.import_path == import_path
    assert pp.resource_name == resource_name


@pytest.mark.parametrize(
    "original_url, expected_content_path_suffix",
    [
        ("py://tests/resources/empty-style.toml", "tests/resources/empty-style.toml"),
        ("py://tests/resources/nested_package/empty_style.toml", "tests/resources/nested_package/empty_style.toml"),
        ("pypackage://tests/resources/empty-style.toml", "tests/resources/empty-style.toml"),
        (
            "pypackage://tests/resources/nested_package/empty_style.toml",
            "tests/resources/nested_package/empty_style.toml",
        ),
    ],
)
def test_raw_content_url_of_python_package(original_url, expected_content_path_suffix):
    """Test ``PythonPackageURL`` can return valid path."""
    pp = PythonPackageURL.from_furl(furl(original_url))
    expected_content_path = Path(__file__).parent.parent / expected_content_path_suffix
    assert pp.content_path == expected_content_path


def test_protocol_not_supported(tmp_path):
    """Test unsupported protocols."""
    project = ProjectMock(tmp_path).pyproject_toml(
        """
        [tool.nitpick]
        style = ["abc://www.example.com/style.toml"]
        """
    )
    with pytest.raises(RuntimeError) as exc_info:
        project.api_check()
    assert str(exc_info.value) == "URL protocol 'abc' is not supported"
