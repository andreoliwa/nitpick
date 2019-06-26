"""JSON tests."""
from tests.helpers import ProjectMock


def test_suggest_initial_contents(request):
    """Suggest initial contents for missing JSON file."""
    pass  # FIXME:


def test_missing_different_values(request):
    """Test missing and different values."""
    ProjectMock(request).load_styles("package-json").pyproject_toml(
        """
        [tool.nitpick]
        style = ["package-json"]
        """
    ).save_file("package.json", '{"name": "myproject", "version": "0.0.1"}').lint().assert_errors_contain(
        """
        NIP348 File package.json has missing keys:\x1b[92m
        {
          "release": {
            "plugins": "?"
          },
          "repository": {
            "type": "?",
            "url": "?"
          }
        }\x1b[0m
        """
    )
