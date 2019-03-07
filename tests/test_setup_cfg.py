"""setup.cfg tests."""
from flake8_nitpick.files.setup_cfg import SetupCfgFile
from tests.helpers import ProjectMock


def test_setup_cfg_should_be_deleted(request):
    """File should be deleted."""
    ProjectMock(request).style("").setup_cfg("").lint().assert_errors_contain(
        f"NIP322 File {SetupCfgFile.file_name} should be deleted"
    )


def test_comma_separated_keys_on_style_file(request):
    """Comma separated keys on the style file."""
    project = (
        ProjectMock(request)
        .style(
            f"""
            [nitpick.files."{SetupCfgFile.file_name}"]
            comma_separated_values = ["food.eat"]

            ["{SetupCfgFile.file_name}".food]
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
    project.assert_errors_contain(
        f"""
        NIP322 File {SetupCfgFile.file_name} has missing values in the 'eat' key. Include those values:
        [food]
        eat = (...),ham,salt
        """
    )


def test_missing_setup_cfg(request):
    """Suggest contents when {SetupCfgFile.file_name} does not exist."""
    ProjectMock(request).style(
        f"""
        [nitpick.files."{SetupCfgFile.file_name}"]
        "missing_message" = "Do something here"

        ["{SetupCfgFile.file_name}".mypy]
        ignore_missing_imports = true

        ["{SetupCfgFile.file_name}".isort]
        line_length = 120

        ["{SetupCfgFile.file_name}".flake8]
        max-line-length = 120
        """
    ).lint().assert_errors_contain(
        f"""
        NIP321 File {SetupCfgFile.file_name} was not found. Do something here. Create it with this content:
        [flake8]
        max-line-length = 120

        [isort]
        line_length = 120

        [mypy]
        ignore_missing_imports = True
        """
    )
