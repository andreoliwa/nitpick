"""setup.cfg tests."""
from tests.helpers import ProjectMock


def test_setup_cfg_should_be_deleted(request):
    """File should be deleted."""
    ProjectMock(request).style("").setup_cfg("").lint().assert_single_error(f"NIP322 File setup.cfg should be deleted")


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
        .lint()
    )
    project.assert_single_error(
        """
        NIP322 File setup.cfg has missing values in the 'eat' key. Include those values:
        [food]
        eat = (...),ham,salt
        """
    )


def test_missing_setup_cfg(request):
    """Suggest contents when setup.cfg does not exist."""
    ProjectMock(request).style(
        """
        [nitpick.files."setup.cfg"]
        "missing_message" = "Do something here"

        ["setup.cfg".mypy]
        ignore_missing_imports = true

        ["setup.cfg".isort]
        line_length = 120

        ["setup.cfg".flake8]
        max-line-length = 120
        """
    ).lint().assert_single_error(
        """
        NIP321 File setup.cfg was not found. Do something here. Create it with this content:
        [flake8]
        max-line-length = 120

        [isort]
        line_length = 120

        [mypy]
        ignore_missing_imports = True
        """
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
    ).lint().assert_single_error(
        """
        NIP321 File setup.cfg has some missing sections. Use this:
        [flake8]
        max-line-length = 120

        [isort]
        line_length = 120
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
    ).lint().assert_errors_contain(
        """
        NIP323 File setup.cfg: [isort]line_length is 30 but it should be like this:
        [isort]
        line_length = 110
        """
    ).assert_errors_contain(
        """
        NIP324 File setup.cfg: section [flake8] has some missing key/value pairs. Use this:
        [flake8]
        max-line-length = 112
        """
    )
