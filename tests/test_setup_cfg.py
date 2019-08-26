"""setup.cfg tests."""
from tests.helpers import ProjectMock


def test_setup_cfg_has_no_configuration(request):
    """File should not be deleted unless explicitly asked."""
    ProjectMock(request).style("").setup_cfg("").flake8().assert_no_errors()


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
        .flake8()
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
    ).flake8().assert_errors_contain(
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
    ).flake8().assert_single_error(
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
    ).flake8().assert_errors_contain(
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

        ["setup.cfg"]
        comma_separated_values = ["flake8.ignore", "flake8.exclude"]
        """
    ).flake8().assert_errors_contain(
        """
        NIP321 File setup.cfg was not found. Create it with this content:\x1b[32m
        [flake8]
        ignore = D100,D101,D102,D103,D104,D105,D106,D107,D202,E203,W503
        max-complexity = 12
        max-line-length = 85
        select = E241,C,E,F,W,B,B9\x1b[0m
        """
    )
