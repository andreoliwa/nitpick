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
        NIP322 File: setup.cfg: Missing values in key
        [food]
        eat = ham,salt
        """
    )
