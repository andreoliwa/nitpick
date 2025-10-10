"""Test INI files."""

from configparser import ParsingError
from unittest import mock

from configupdater import ConfigUpdater

from nitpick.constants import EDITOR_CONFIG, PYTHON_SETUP_CFG
from nitpick.plugins.ini import IniPlugin, Violations
from nitpick.violations import Fuss, SharedViolations
from tests.helpers import ProjectMock


def test_setup_cfg_has_no_configuration(tmp_path):
    """File should not be deleted unless explicitly asked."""
    ProjectMock(tmp_path).style("").setup_cfg("").api_check_then_fix()


def test_comma_separated_keys_on_style_file(tmp_path):
    """Comma separated keys on the style file."""
    ProjectMock(tmp_path).style(
        f"""
        [nitpick.files."{PYTHON_SETUP_CFG}"]
        comma_separated_values = ["food.eat", "food.drink"]

        ["{PYTHON_SETUP_CFG}".food]
        eat = "salt,ham,eggs"
        drink = "water,bier,wine"
        """
    ).setup_cfg(
        """
        [food]
        eat = spam,eggs,cheese
        drink =   wine , bier , water
        """
    ).api_check_then_fix(
        Fuss(
            True,
            PYTHON_SETUP_CFG,
            Violations.MISSING_VALUES_IN_LIST.code,
            " has missing values in the 'eat' key. Include those values:",
            """
            [food]
            eat = (...),ham,salt
            """,
        )
    ).assert_file_contents(
        PYTHON_SETUP_CFG,
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
        your_string = value
        your_number = 123
    """
    expected_editor_config = """
        [*]
        end_of_line = lf
        insert_final_newline = True
    """
    ProjectMock(tmp_path).style(
        f"""
        ["{PYTHON_SETUP_CFG}".mypy]
        ignore_missing_imports = true

        ["{PYTHON_SETUP_CFG}".isort]
        line_length = 120

        ["{PYTHON_SETUP_CFG}".flake8]
        max-line-length = 120

        ["generic.ini".your-section]
        your_string = "value"
        your_number = 123

        ["{EDITOR_CONFIG}"."*"]
        end_of_line = "lf"
        insert_final_newline = true
        """
    ).api_check_then_fix(
        Fuss(
            True,
            PYTHON_SETUP_CFG,
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
        PYTHON_SETUP_CFG, expected_setup_cfg, "generic.ini", expected_generic_ini, EDITOR_CONFIG, expected_editor_config
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
        ["{PYTHON_SETUP_CFG}".mypy]
        ignore_missing_imports = true

        ["{PYTHON_SETUP_CFG}".isort]
        line_length = 120

        ["{PYTHON_SETUP_CFG}".flake8]
        max-line-length = 120
        """
    ).api_check_then_fix(
        Fuss(
            True,
            PYTHON_SETUP_CFG,
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
        PYTHON_SETUP_CFG,
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
        ["{PYTHON_SETUP_CFG}".mypy]
        ignore_missing_imports = true

        ["{PYTHON_SETUP_CFG}".isort]
        line_length = 110
        name = "Mary"

        ["{PYTHON_SETUP_CFG}".flake8]
        max-line-length = 112
        """
    ).api_check_then_fix(
        Fuss(
            True,
            PYTHON_SETUP_CFG,
            Violations.OPTION_HAS_DIFFERENT_VALUE.code,
            ": [isort]line_length is 30 but it should be like this:",
            """
            [isort]
            line_length = 110
            """,
        ),
        Fuss(
            True,
            PYTHON_SETUP_CFG,
            Violations.MISSING_OPTION.code,
            ": section [flake8] has some missing key/value pairs. Use this:",
            """
            [flake8]
            max-line-length = 112
            """,
        ),
        Fuss(
            True,
            PYTHON_SETUP_CFG,
            Violations.OPTION_HAS_DIFFERENT_VALUE.code,
            ": [isort]name is John but it should be like this:",
            """
            [isort]
            name = Mary
            """,
        ),
    ).assert_file_contents(
        PYTHON_SETUP_CFG,
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


def test_missing_different_values_editorconfig_with_root(tmp_path, datadir):
    """Test different and missing keys/values for .editorconfig with root values."""
    ProjectMock(tmp_path).save_file(EDITOR_CONFIG, datadir / "2-actual-editorconfig.ini").style(
        datadir / "2-style.toml"
    ).api_check_then_fix(
        Fuss(True, EDITOR_CONFIG, 327, ": root is false but it should be:", "root = True"),
        Fuss(
            True,
            EDITOR_CONFIG,
            Violations.OPTION_HAS_DIFFERENT_VALUE.code,
            ": [*]end_of_line is cr but it should be like this:",
            """
            [*]
            end_of_line = lf
            """,
        ),
        Fuss(
            True,
            EDITOR_CONFIG,
            Violations.OPTION_HAS_DIFFERENT_VALUE.code,
            ": [*]insert_final_newline is false but it should be like this:",
            """
            [*]
            insert_final_newline = True
            """,
        ),
        Fuss(
            True,
            EDITOR_CONFIG,
            Violations.OPTION_HAS_DIFFERENT_VALUE.code,
            ": [*]tab_width is 2 but it should be like this:",
            """
            [*]
            tab_width = 4
            """,
        ),
        Fuss(
            True,
            EDITOR_CONFIG,
            Violations.MISSING_OPTION.code,
            ": section [*.{js,json}] has some missing key/value pairs. Use this:",
            """
            [*.{js,json}]
            indent_size = 2
            """,
        ),
        Fuss(
            True,
            EDITOR_CONFIG,
            Violations.TOP_SECTION_MISSING_OPTION.code,
            ": top section has missing options. Use this:",
            """
            missing = value
            another_missing = 100
            """,
        ),
    ).assert_file_contents(
        EDITOR_CONFIG, datadir / "2-expected-editorconfig.ini"
    )


def test_invalid_configuration_comma_separated_values(tmp_path):
    """Test an invalid configuration for comma_separated_values."""
    ProjectMock(tmp_path).style(
        f"""
        ["{PYTHON_SETUP_CFG}".flake8]
        max-line-length = 85
        max-complexity = 12
        ignore = "D100,D101,D102,D103,D104,D105,D106,D107,D202,E203,W503"
        select = "E241,C,E,F,W,B,B9"

        [nitpick.files."{PYTHON_SETUP_CFG}"]
        comma_separated_values = ["flake8.ignore", "flake8.exclude"]
        """
    ).api_check().assert_violations(
        Fuss(
            False,
            PYTHON_SETUP_CFG,
            321,
            " was not found. Create it with this content:",
            """
            [flake8]
            max-line-length = 85
            max-complexity = 12
            ignore = D100,D101,D102,D103,D104,D105,D106,D107,D202,E203,W503
            select = E241,C,E,F,W,B,B9
            """,
        )
    )


def test_invalid_section_dot_fields(tmp_path):
    """Test invalid section/field pairs."""
    ProjectMock(tmp_path).style(
        f"""
        [nitpick.files."{PYTHON_SETUP_CFG}"]
        comma_separated_values = ["no_dot", "multiple.dots.here", ".filed_only", "section_only."]
        """
    ).setup_cfg("").api_check().assert_violations(
        Fuss(
            False,
            "nitpick-style.toml",
            1,
            " has an incorrect style. Invalid config:",
            f"""
            nitpick.files."{PYTHON_SETUP_CFG}".comma_separated_values.0: Dot is missing. Use <section_name>.<field_name>
            nitpick.files."{PYTHON_SETUP_CFG}".comma_separated_values.1: There's more than one dot. Use <section_name>.<field_name>
            nitpick.files."{PYTHON_SETUP_CFG}".comma_separated_values.2: Empty section name. Use <section_name>.<field_name>
            nitpick.files."{PYTHON_SETUP_CFG}".comma_separated_values.3: Empty field name. Use <section_name>.<field_name>
            """,
        )
    )


def test_invalid_sections_comma_separated_values(tmp_path):
    """Test invalid sections on comma_separated_values."""
    ProjectMock(tmp_path).style(
        f"""
        ["{PYTHON_SETUP_CFG}".flake8]
        ignore = "W503,E203,FI58,PT003,C408"
        exclude = "venv*,**/migrations/"
        per-file-ignores = "tests/**.py:FI18,setup.py:FI18"

        [nitpick.files."{PYTHON_SETUP_CFG}"]
        comma_separated_values = ["flake8.ignore", "flake8.exclude", "falek8.per-file-ignores", "aaa.invalid-section"]
        """
    ).setup_cfg(
        """
        [flake8]
        exclude = venv*,**/migrations/
        ignore = W503,E203,FI12,FI15,FI16,FI17,FI18,FI50,FI51,FI53,FI54,FI55,FI58,PT003,C408
        per-file-ignores = tests/**.py:FI18,setup.py:FI18,tests/**.py:BZ01
        """
    ).api_check_then_fix(
        Fuss(False, PYTHON_SETUP_CFG, 325, ": invalid sections on comma_separated_values:", "aaa, falek8")
    )


def test_multiline_comment(tmp_path, datadir):
    """Test file with multiline comments should not raise a configparser.ParsingError."""
    ProjectMock(tmp_path).style(
        f"""
        ["{PYTHON_SETUP_CFG}".flake8]
        new = "value"
        """
    ).setup_cfg(datadir / "3-actual-setup.cfg").api_fix().assert_violations(
        Fuss(
            True,
            PYTHON_SETUP_CFG,
            324,
            ": section [flake8] has some missing key/value pairs. Use this:",
            """
            [flake8]
            new = value
            """,
        )
    ).assert_file_contents(
        PYTHON_SETUP_CFG, datadir / "3-expected-setup.cfg"
    )


def test_duplicated_option(tmp_path):
    """Test a violation is raised if a file has a duplicated option."""
    original_file = """
        [abc]
        easy = 123
        easy = as sunday morning
        """
    project = ProjectMock(tmp_path)
    project.style(
        f"""
        ["{PYTHON_SETUP_CFG}".abc]
        hard = "as a rock"
        """
    ).setup_cfg(original_file).api_fix().assert_violations(
        Fuss(
            False,
            PYTHON_SETUP_CFG,
            Violations.PARSING_ERROR.code,
            f": parsing error (DuplicateOptionError): While reading from {project.path_for(PYTHON_SETUP_CFG)!r} "
            f"[line  3]: option 'easy' in section 'abc' already exists",
        )
    ).assert_file_contents(
        PYTHON_SETUP_CFG, original_file
    )


@mock.patch.object(ConfigUpdater, "update_file")
def test_simulate_parsing_error_when_saving(update_file, tmp_path):
    """Simulate a parsing error when saving an INI file."""
    update_file.side_effect = ParsingError(source="simulating a captured error")

    original_file = """
        [flake8]
        existing = value
        """
    ProjectMock(tmp_path).style(
        f"""
        ["{PYTHON_SETUP_CFG}".flake8]
        new = "value"
        """
    ).setup_cfg(original_file).api_fix().assert_violations(
        Fuss(
            True,
            PYTHON_SETUP_CFG,
            324,
            ": section [flake8] has some missing key/value pairs. Use this:",
            """
            [flake8]
            new = value
            """,
        ),
        Fuss(
            False,
            PYTHON_SETUP_CFG,
            Violations.PARSING_ERROR.code,
            ": parsing error (ParsingError): Source contains parsing errors: 'simulating a captured error'",
        ),
    ).assert_file_contents(
        PYTHON_SETUP_CFG, original_file
    )


def test_generic_ini_with_missing_header(tmp_path):
    """A generic .ini with a missing header should raise a violation."""
    expected_generic_ini = """
        this_key_is_invalid = for a generic .ini (it should always have a section)

        [your-section]
        your_number = 200
        your_string = value
    """
    project = ProjectMock(tmp_path)
    project.save_file("generic.ini", expected_generic_ini).style(
        """
        ["generic.ini".your-section]
        your_string = "value"
        your_number = 100
        """
    ).api_check_then_fix(
        Fuss(
            False,
            "generic.ini",
            Violations.PARSING_ERROR.code,
            ": parsing error (MissingSectionHeaderError): File contains no section headers.\n"
            f"file: {project.path_for('generic.ini')!r}, line: 1\n"
            "'this_key_is_invalid = for a generic .ini (it should always have a section)\\n'",
        )
    ).assert_file_contents(
        "generic.ini", expected_generic_ini
    )


def test_add_options_with_multiple_trailing_spaces(tmp_path):
    """Test that adding options works correctly when there are multiple trailing spaces.

    This is a regression test for the NotAttachedError bug that occurred when
    trying to detach multiple consecutive Space blocks.
    """
    ProjectMock(tmp_path).setup_cfg(
        """
        [flake8]
        max-line-length = 100


        """
    ).style(
        f"""
        ["{PYTHON_SETUP_CFG}".flake8]
        max-line-length = 100
        max-complexity = 10
        """
    ).api_check_then_fix(
        Fuss(
            True,
            PYTHON_SETUP_CFG,
            Violations.MISSING_OPTION.code,
            ": section [flake8] has some missing key/value pairs. Use this:",
            """
            [flake8]
            max-complexity = 10
            """,
        )
    ).assert_file_contents(
        PYTHON_SETUP_CFG,
        """
        [flake8]
        max-line-length = 100
        max-complexity = 10
        """,
    )
