"""JSON tests."""
from tests.helpers import ProjectMock


def test_suggest_initial_contents(request):
    """Suggest initial contents for missing JSON file."""
    ProjectMock(request).load_styles("package-json").pyproject_toml(
        """
        [tool.nitpick]
        style = ["package-json"]
        """
    ).lint().assert_errors_contain(
        """
        NIP341 File package.json was not found. Create it with this content:\x1b[92m
        {
          "name": "<some value here>",
          "release": {
            "plugins": "<some value here>"
          },
          "repository": {
            "type": "<some value here>",
            "url": "<some value here>"
          },
          "version": "<some value here>"
        }\x1b[0m
        """
    )


def test_json_file_contains_keys(request):
    """Test if JSON file contains keys."""
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
            "plugins": "<some value here>"
          },
          "repository": {
            "type": "<some value here>",
            "url": "<some value here>"
          }
        }\x1b[0m
        """
    )
