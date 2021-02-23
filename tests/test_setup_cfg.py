"""setup.cfg tests."""
from nitpick.constants import SETUP_CFG
from nitpick.plugins.setup_cfg import SetupCfgPlugin, Violations
from nitpick.violations import Fuss, ProjectViolations, SharedViolations
from tests.helpers import XFAIL_ON_WINDOWS, ProjectMock


def test_setup_cfg_has_no_configuration(tmp_path):
    """File should not be deleted unless explicitly asked."""
    ProjectMock(tmp_path).style("").setup_cfg("").api_check_then_apply()


@XFAIL_ON_WINDOWS
def test_default_style_is_applied(project_with_default_style):
    """Test if the default style is applied on an empty project."""
    expected_content = """
        [flake8]
        exclude = .tox,build
        ignore = D107,D202,D203,D401,E203,E402,E501,W503
        inline-quotes = double
        max-line-length = 120

        [isort]
        combine_as_imports = True
        force_grid_wrap = 0
        include_trailing_comma = True
        known_first_party = tests
        line_length = 120
        multi_line_output = 3
        skip = .tox,build

        [mypy]
        follow_imports = skip
        ignore_missing_imports = True
        strict_optional = True
        warn_no_return = True
        warn_redundant_casts = True
        warn_unused_ignores = True
    """
    project_with_default_style.api_check_then_apply(
        Fuss(
            fixed=True,
            filename="setup.cfg",
            code=321,
            message=" was not found. Create it with this content:",
            suggestion=expected_content,
            lineno=1,
        ),
        partial_names=[SETUP_CFG],
    ).assert_file_contents(SETUP_CFG, expected_content)


def test_comma_separated_keys_on_style_file(tmp_path):
    """Comma separated keys on the style file."""
    ProjectMock(tmp_path).style(
        """
        [nitpick.files."setup.cfg"]
        comma_separated_values = ["food.eat"]

        ["setup.cfg".food]
        eat = "salt,ham,eggs"
        """
    ).setup_cfg(
        """
        [food]
        eat = spam,eggs,cheese
        """
    ).api_check_then_apply(
        Fuss(
            True,
            SETUP_CFG,
            Violations.MISSING_VALUES_IN_LIST.code,
            " has missing values in the 'eat' key. Include those values:",
            """
            [food]
            eat = (...),ham,salt
            """,
        )
    ).assert_file_contents(
        SETUP_CFG,
        """
        [food]
        eat = spam,eggs,cheese,ham,salt
        """,
    )


def test_suggest_initial_contents(tmp_path):
    """Suggest contents when setup.cfg does not exist."""
    expected_content = """
        [flake8]
        max-line-length = 120

        [isort]
        line_length = 120

        [mypy]
        ignore_missing_imports = True
    """
    ProjectMock(tmp_path).style(
        """
        [nitpick.files.present]
        "setup.cfg" = "Do something here"

        ["setup.cfg".mypy]
        ignore_missing_imports = true

        ["setup.cfg".isort]
        line_length = 120

        ["setup.cfg".flake8]
        max-line-length = 120
        """
    ).api_check_then_apply(
        Fuss(
            True,
            SETUP_CFG,
            SharedViolations.CREATE_FILE_WITH_SUGGESTION.code + SetupCfgPlugin.violation_base_code,
            " was not found. Create it with this content:",
            expected_content,
        ),
        Fuss(False, SETUP_CFG, ProjectViolations.MISSING_FILE.code, " should exist: Do something here"),
    ).assert_file_contents(
        SETUP_CFG, expected_content
    )


def test_missing_sections(tmp_path):
    """Test missing sections."""
    ProjectMock(tmp_path).setup_cfg(
        """
        [mypy]
        ignore_missing_imports = true
        """
    ).style(
        """
        ["setup.cfg".mypy]
        ignore_missing_imports = true

        ["setup.cfg".isort]
        line_length = 120

        ["setup.cfg".flake8]
        max-line-length = 120
        """
    ).api_check_then_apply(
        Fuss(
            True,
            SETUP_CFG,
            Violations.MISSING_SECTIONS.code,
            " has some missing sections. Use this:",
            """
            [flake8]
            max-line-length = 120

            [isort]
            line_length = 120
            """,
        )
    ).assert_file_contents(
        SETUP_CFG,
        """
        [mypy]
        ignore_missing_imports = true

        [flake8]
        max-line-length = 120

        [isort]
        line_length = 120
        """,
    )


def test_missing_different_values(tmp_path):
    """Test different and missing keys/values."""
    ProjectMock(tmp_path).setup_cfg(
        """
        [mypy]
        # Line comment with hash (inline comments are not supported)
        ignore_missing_imports = true

        [isort]
        line_length = 30
        [flake8]
        ; Line comment with semicolon
        xxx = "aaa"
        """
    ).style(
        """
        ["setup.cfg".mypy]
        ignore_missing_imports = true

        ["setup.cfg".isort]
        line_length = 110

        ["setup.cfg".flake8]
        max-line-length = 112
        """
    ).api_check_then_apply(
        Fuss(
            True,
            SETUP_CFG,
            Violations.KEY_HAS_DIFFERENT_VALUE.code,
            ": [isort]line_length is 30 but it should be like this:",
            """
            [isort]
            line_length = 110
            """,
        ),
        Fuss(
            True,
            SETUP_CFG,
            Violations.MISSING_KEY_VALUE_PAIRS.code,
            ": section [flake8] has some missing key/value pairs. Use this:",
            """
            [flake8]
            max-line-length = 112
            """,
        ),
    ).assert_file_contents(
        SETUP_CFG,
        """
        [mypy]
        # Line comment with hash (inline comments are not supported)
        ignore_missing_imports = true

        [isort]
        line_length = 110
        [flake8]
        ; Line comment with semicolon
        xxx = "aaa"
        max-line-length = 112
        """,
    )


def test_invalid_configuration_comma_separated_values(tmp_path):
    """Test an invalid configuration for comma_separated_values."""
    ProjectMock(tmp_path).style(
        """
        ["setup.cfg".flake8]
        max-line-length = 85
        max-complexity = 12
        ignore = "D100,D101,D102,D103,D104,D105,D106,D107,D202,E203,W503"
        select = "E241,C,E,F,W,B,B9"

        [nitpick.files."setup.cfg"]
        comma_separated_values = ["flake8.ignore", "flake8.exclude"]
        """
    ).api_check().assert_violations(
        Fuss(
            False,
            SETUP_CFG,
            321,
            " was not found. Create it with this content:",
            """
            [flake8]
            ignore = D100,D101,D102,D103,D104,D105,D106,D107,D202,E203,W503
            max-complexity = 12
            max-line-length = 85
            select = E241,C,E,F,W,B,B9
            """,
        )
    )


def test_invalid_section_dot_fields(tmp_path):
    """Test invalid section/field pairs."""
    ProjectMock(tmp_path).style(
        """
        [nitpick.files."setup.cfg"]
        comma_separated_values = ["no_dot", "multiple.dots.here", ".filed_only", "section_only."]
        """
    ).setup_cfg("").api_check().assert_violations(
        Fuss(
            False,
            "nitpick-style.toml",
            1,
            " has an incorrect style. Invalid config:",
            """
            nitpick.files."setup.cfg".comma_separated_values.0: Dot is missing. Use <section_name>.<field_name>
            nitpick.files."setup.cfg".comma_separated_values.1: There's more than one dot. Use <section_name>.<field_name>
            nitpick.files."setup.cfg".comma_separated_values.2: Empty section name. Use <section_name>.<field_name>
            nitpick.files."setup.cfg".comma_separated_values.3: Empty field name. Use <section_name>.<field_name>
            """,
        )
    )


def test_invalid_sections_comma_separated_values(tmp_path):
    """Test invalid sections on comma_separated_values."""
    ProjectMock(tmp_path).style(
        """
        ["setup.cfg".flake8]
        ignore = "W503,E203,FI58,PT003,C408"
        exclude = "venv*,**/migrations/"
        per-file-ignores = "tests/**.py:FI18,setup.py:FI18"

        [nitpick.files."setup.cfg"]
        comma_separated_values = ["flake8.ignore", "flake8.exclude", "falek8.per-file-ignores", "aaa.invalid-section"]
        """
    ).setup_cfg(
        """
        [flake8]
        exclude = venv*,**/migrations/
        ignore = W503,E203,FI12,FI15,FI16,FI17,FI18,FI50,FI51,FI53,FI54,FI55,FI58,PT003,C408
        per-file-ignores = tests/**.py:FI18,setup.py:FI18,tests/**.py:BZ01
        """
    ).api_check_then_apply(
        Fuss(False, SETUP_CFG, 325, ": invalid sections on comma_separated_values:", "aaa, falek8")
    )
