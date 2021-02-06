"""setup.cfg tests."""
from tests.helpers import ProjectMock


def test_setup_cfg_has_no_configuration(request):
    """File should not be deleted unless explicitly asked."""
    ProjectMock(request).style("").setup_cfg("").simulate_run().assert_no_errors()


def test_comma_separated_keys_on_style_file(request):
    """Comma separated keys on the style file."""
    project = (
        ProjectMock(request)
        .style(
            """
            [nitpick.files."setup.cfg"]
            comma_separated_values = ["food.eat"]

            ["setup.cfg".food]
            eat = "salt,ham,eggs"
            """
        )
        .setup_cfg(
            """
            [food]
            eat = spam,eggs,cheese
            """
        )
        .simulate_run()
    )
    project.assert_single_error(
        """
        NIP322 File setup.cfg has missing values in the 'eat' key. Include those values:\x1b[32m
        [food]
        eat = (...),ham,salt\x1b[0m
        """
    )


def test_suggest_initial_contents(request):
    """Suggest contents when setup.cfg does not exist."""
    ProjectMock(request).style(
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
    ).simulate_run().assert_errors_contain(
        """
        NIP321 File setup.cfg was not found. Create it with this content:\x1b[32m
        [flake8]
        max-line-length = 120

        [isort]
        line_length = 120

        [mypy]
        ignore_missing_imports = True\x1b[0m
        """,
        2,
    ).assert_errors_contain(
        "NIP103 File setup.cfg should exist: Do something here"
    )


def test_missing_sections(request):
    """Test missing sections."""
    ProjectMock(request).setup_cfg(
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
    ).simulate_run().assert_single_error(
        """
        NIP321 File setup.cfg has some missing sections. Use this:\x1b[32m
        [flake8]
        max-line-length = 120

        [isort]
        line_length = 120\x1b[0m
        """
    )


def test_different_missing_keys(request):
    """Test different and missing keys."""
    ProjectMock(request).setup_cfg(
        """
        [mypy]
        ignore_missing_imports = true
        [isort]
        line_length = 30
        [flake8]
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
    ).simulate_run().assert_errors_contain(
        """
        NIP323 File setup.cfg: [isort]line_length is 30 but it should be like this:\x1b[32m
        [isort]
        line_length = 110\x1b[0m
        """
    ).assert_errors_contain(
        """
        NIP324 File setup.cfg: section [flake8] has some missing key/value pairs. Use this:\x1b[32m
        [flake8]
        max-line-length = 112\x1b[0m
        """
    )


def test_invalid_configuration_comma_separated_values(request):
    """Test an invalid configuration for comma_separated_values."""
    ProjectMock(request).style(
        """
        ["setup.cfg".flake8]
        max-line-length = 85
        max-complexity = 12
        ignore = "D100,D101,D102,D103,D104,D105,D106,D107,D202,E203,W503"
        select = "E241,C,E,F,W,B,B9"

        [nitpick.files."setup.cfg"]
        comma_separated_values = ["flake8.ignore", "flake8.exclude"]
        """
    ).simulate_run().assert_errors_contain(
        """
        NIP321 File setup.cfg was not found. Create it with this content:\x1b[32m
        [flake8]
        ignore = D100,D101,D102,D103,D104,D105,D106,D107,D202,E203,W503
        max-complexity = 12
        max-line-length = 85
        select = E241,C,E,F,W,B,B9\x1b[0m
        """
    )


def test_invalid_section_dot_fields(request):
    """Test invalid section/field pairs."""
    ProjectMock(request).style(
        """
        [nitpick.files."setup.cfg"]
        comma_separated_values = ["no_dot", "multiple.dots.here", ".filed_only", "section_only."]
        """
    ).setup_cfg("").simulate_run().assert_errors_contain(
        """
        NIP001 File nitpick-style.toml has an incorrect style. Invalid config:\x1b[32m
        nitpick.files."setup.cfg".comma_separated_values.0: Dot is missing. Use <section_name>.<field_name>
        nitpick.files."setup.cfg".comma_separated_values.1: There's more than one dot. Use <section_name>.<field_name>
        nitpick.files."setup.cfg".comma_separated_values.2: Empty section name. Use <section_name>.<field_name>
        nitpick.files."setup.cfg".comma_separated_values.3: Empty field name. Use <section_name>.<field_name>\x1b[0m
        """
    )


def test_invalid_sections_comma_separated_values(request):
    """Test invalid sections on comma_separated_values."""
    ProjectMock(request).style(
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
    ).simulate_run().assert_single_error(
        "NIP325 File setup.cfg: invalid sections on comma_separated_values:\x1b[32m\naaa, falek8\x1b[0m"
    )
