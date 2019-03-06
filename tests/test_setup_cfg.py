"""setup.cfg tests."""
from tests.helpers import ProjectMock


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
    project.assert_errors_contain(
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
    ).lint().assert_errors_contain(
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
