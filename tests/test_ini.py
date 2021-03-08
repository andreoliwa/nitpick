"""setup.cfg tests."""
from configparser import ParsingError
from unittest import mock

from configupdater import ConfigUpdater

from nitpick.constants import EDITOR_CONFIG, SETUP_CFG
from nitpick.plugins.ini import IniPlugin, Violations
from nitpick.violations import Fuss, SharedViolations
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
        Fuss(True, SETUP_CFG, 321, " was not found. Create it with this content:", expected_content),
        partial_names=[SETUP_CFG],
    ).assert_file_contents(SETUP_CFG, expected_content)


def test_comma_separated_keys_on_style_file(tmp_path):
    """Comma separated keys on the style file."""
    ProjectMock(tmp_path).style(
        """
        [nitpick.files."setup.cfg"]
        comma_separated_values = ["food.eat", "food.drink"]

        ["setup.cfg".food]
        eat = "salt,ham,eggs"
        drink = "water,bier,wine"
        """
    ).setup_cfg(
        """
        [food]
        eat = spam,eggs,cheese
        drink =   wine , bier , water
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
        drink =   wine , bier , water
        """,
    )


def test_suggest_initial_contents(tmp_path):
    """Suggest contents when INI files do not exist."""
    expected_setup_cfg = """
        [flake8]
        max-line-length = 120

        [isort]
        line_length = 120

        [mypy]
        ignore_missing_imports = True
    """
    expected_generic_ini = """
        [your-section]
        your_number = 123
        your_string = value
    """
    expected_editor_config = """
        [*]
        end_of_line = lf
        insert_final_newline = True
    """
    ProjectMock(tmp_path).style(
        f"""
        ["{SETUP_CFG}".mypy]
        ignore_missing_imports = true

        ["{SETUP_CFG}".isort]
        line_length = 120

        ["{SETUP_CFG}".flake8]
        max-line-length = 120

        ["generic.ini".your-section]
        your_string = "value"
        your_number = 123

        ["{EDITOR_CONFIG}"."*"]
        end_of_line = "lf"
        insert_final_newline = true
        """
    ).api_check_then_apply(
        Fuss(
            True,
            SETUP_CFG,
            SharedViolations.CREATE_FILE_WITH_SUGGESTION.code + IniPlugin.violation_base_code,
            " was not found. Create it with this content:",
            expected_setup_cfg,
        ),
        Fuss(
            True,
            "generic.ini",
            SharedViolations.CREATE_FILE_WITH_SUGGESTION.code + IniPlugin.violation_base_code,
            " was not found. Create it with this content:",
            expected_generic_ini,
        ),
        Fuss(
            True,
            EDITOR_CONFIG,
            SharedViolations.CREATE_FILE_WITH_SUGGESTION.code + IniPlugin.violation_base_code,
            " was not found. Create it with this content:",
            expected_editor_config,
        ),
    ).assert_file_contents(
        SETUP_CFG, expected_setup_cfg, "generic.ini", expected_generic_ini, EDITOR_CONFIG, expected_editor_config
    )


def test_missing_sections(tmp_path):
    """Test missing sections."""
    ProjectMock(tmp_path).setup_cfg(
        """
        [mypy]
        ignore_missing_imports = true
        """
    ).style(
        f"""
        ["{SETUP_CFG}".mypy]
        ignore_missing_imports = true

        ["{SETUP_CFG}".isort]
        line_length = 120

        ["{SETUP_CFG}".flake8]
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
        name = John
        [flake8]
        ; Line comment with semicolon
        xxx = "aaa"
        """
    ).style(
        f"""
        ["{SETUP_CFG}".mypy]
        ignore_missing_imports = true

        ["{SETUP_CFG}".isort]
        line_length = 110
        name = "Mary"

        ["{SETUP_CFG}".flake8]
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
        Fuss(
            True,
            SETUP_CFG,
            Violations.KEY_HAS_DIFFERENT_VALUE.code,
            ": [isort]name is John but it should be like this:",
            """
            [isort]
            name = Mary
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
        name = Mary
        [flake8]
        ; Line comment with semicolon
        xxx = "aaa"
        max-line-length = 112
        """,
    )


def test_missing_different_values_editorconfig_with_root(tmp_path):
    """Test different and missing keys/values for .editorconfig with root values."""
    ProjectMock(tmp_path).save_file(
        EDITOR_CONFIG,
        """
        # Comments should be kept
        root = false
        some_other = "value without a section"

        [*]
        ; Another comment that should be kept
        end_of_line = cr
        insert_final_newline = false
        indent_style = space
        tab_width = 2
        indent_size = tab

        [*.{js,json}]
        charset = utf-8
        """,
    ).style(
        f"""
        ["{EDITOR_CONFIG}"]
        root = true

        ["{EDITOR_CONFIG}"."*"]
        end_of_line = "lf"
        insert_final_newline = true
        tab_width = 4

        ["{EDITOR_CONFIG}"."*.{{js,json}}"]
        charset = "utf-8"
        indent_size = 2
        """
    ).api_check_then_apply(
        Fuss(True, EDITOR_CONFIG, 327, ": root is false but it should be:", "root = True"),
        Fuss(
            True,
            EDITOR_CONFIG,
            323,
            ": [*]end_of_line is cr but it should be like this:",
            """
            [*]
            end_of_line = lf
            """,
        ),
        Fuss(
            True,
            EDITOR_CONFIG,
            323,
            ": [*]insert_final_newline is false but it should be like this:",
            """
            [*]
            insert_final_newline = True
            """,
        ),
        Fuss(
            True,
            EDITOR_CONFIG,
            323,
            ": [*]tab_width is 2 but it should be like this:",
            """
            [*]
            tab_width = 4
            """,
        ),
        Fuss(
            True,
            EDITOR_CONFIG,
            324,
            ": section [*.{js,json}] has some missing key/value pairs. Use this:",
            """
            [*.{js,json}]
            indent_size = 2
            """,
        ),
    ).assert_file_contents(
        EDITOR_CONFIG,
        """
        # Comments should be kept
        root = true
        some_other = "value without a section"

        [*]
        ; Another comment that should be kept
        end_of_line = lf
        insert_final_newline = true
        indent_style = space
        tab_width = 4
        indent_size = tab

        [*.{js,json}]
        charset = utf-8
        indent_size = 2
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


def test_multiline_comment(tmp_path):
    """Test file with multiline comments should not raise a configparser.ParsingError."""
    original_file = """
        [flake8]
        exclude =
          # Trash and cache:
          .git
          __pycache__
          .venv
          .eggs
          *.egg
          temp
          # Bad code that I write to test things:
          ex.py
        another =
            A valid line
            ; Now a comment with semicolon
            Another valid line
        """
    ProjectMock(tmp_path).style(
        """
        ["setup.cfg".flake8]
        new = "value"
        """
    ).setup_cfg(original_file).api_apply().assert_violations(
        Fuss(
            True,
            SETUP_CFG,
            324,
            ": section [flake8] has some missing key/value pairs. Use this:",
            """
            [flake8]
            new = value
            """,
        )
    ).assert_file_contents(
        SETUP_CFG,
        f"""
        {original_file}new = value
        """,
    )


def test_duplicated_option(tmp_path):
    """Test a violation is raised if a file has a duplicated option."""
    original_file = """
        [abc]
        easy = 123
        easy = as sunday morning
        """
    project = ProjectMock(tmp_path)
    full_path = project.root_dir / SETUP_CFG
    project.style(
        """
        ["setup.cfg".abc]
        hard = "as a rock"
        """
    ).setup_cfg(original_file).api_apply().assert_violations(
        Fuss(
            False,
            SETUP_CFG,
            Violations.PARSING_ERROR.code,
            f": parsing error (DuplicateOptionError): While reading from {str(full_path)!r} "
            f"[line  3]: option 'easy' in section 'abc' already exists",
        )
    ).assert_file_contents(
        SETUP_CFG, original_file
    )


@mock.patch.object(ConfigUpdater, "update_file")
def test_simulate_parsing_error_when_saving(update_file, tmp_path):
    """Simulate a parsing error when saving setup.cfg."""
    update_file.side_effect = ParsingError(source="simulating a captured error")

    original_file = """
        [flake8]
        existing = value
        """
    ProjectMock(tmp_path).style(
        """
        ["setup.cfg".flake8]
        new = "value"
        """
    ).setup_cfg(original_file).api_apply().assert_violations(
        Fuss(
            True,
            SETUP_CFG,
            324,
            ": section [flake8] has some missing key/value pairs. Use this:",
            """
            [flake8]
            new = value
            """,
        ),
        Fuss(
            False,
            SETUP_CFG,
            Violations.PARSING_ERROR.code,
            ": parsing error (ParsingError): Source contains parsing errors: 'simulating a captured error'",
        ),
    ).assert_file_contents(
        SETUP_CFG, original_file
    )
