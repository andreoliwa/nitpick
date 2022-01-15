"""JSON tests."""
import warnings

from nitpick.constants import PACKAGE_JSON, READ_THE_DOCS_URL
from nitpick.plugins.json import JsonPlugin
from nitpick.violations import Fuss, SharedViolations
from tests.helpers import ProjectMock


def test_suggest_initial_contents(tmp_path, datadir):
    """Suggest initial contents for missing JSON file."""
    expected_package_json = (datadir / "1-expected-package.json").read_text()
    ProjectMock(tmp_path).named_style("package-json", datadir / "package-json-style.toml").pyproject_toml(
        """
        [tool.nitpick]
        style = ["package-json"]
        """
    ).api_check_then_fix(
        Fuss(
            True,
            PACKAGE_JSON,
            341,
            " was not found. Create it with this content:",
            expected_package_json,
        )
    ).assert_file_contents(
        PACKAGE_JSON, expected_package_json
    ).api_check_then_fix()


def test_missing_different_values_with_contains_json_with_contains_keys(tmp_path, datadir):
    """Test missing and different values with "contains_json" and "contains_keys"."""
    expected_package_json = (datadir / "2-expected-package.json").read_text()
    ProjectMock(tmp_path).named_style("package-json", datadir / "package-json-style.toml").pyproject_toml(
        """
        [tool.nitpick]
        style = ["package-json"]
        """
    ).save_file(PACKAGE_JSON, datadir / "2-actual-package.json").api_check_then_fix(
        Fuss(
            True,
            PACKAGE_JSON,
            SharedViolations.MISSING_VALUES.code + JsonPlugin.violation_base_code,
            " has missing values:",
            """
            {
              "release": {
                "plugins": "<some value here>"
              },
              "repository": {
                "type": "<some value here>",
                "url": "<some value here>"
              }
            }
            """,
        ),
        Fuss(
            True,
            PACKAGE_JSON,
            348,
            " has missing values:",
            """
            {
              "commitlint": {
                "extends": [
                  "@commitlint/config-conventional"
                ]
              }
            }
            """,
        ),
    ).assert_file_contents(
        PACKAGE_JSON, expected_package_json
    ).api_check_then_fix()


def test_missing_different_values_with_contains_json_without_contains_keys(tmp_path, datadir):
    """Test missing and different values with "contains_json", without "contains_keys"."""
    ProjectMock(tmp_path).style(datadir / "3-style.toml").save_file(
        "my.json", '{"name":"myproject","formatting":{"on.the":"actual file"}}'
    ).api_check_then_fix(
        Fuss(
            True,
            "my.json",
            SharedViolations.MISSING_VALUES.code + JsonPlugin.violation_base_code,
            " has missing values:",
            """
            {
              "formatting": {
                "doesnt": "matter",
                "here": true
              },
              "some.dotted.root.key": {
                "content": [
                  "should",
                  "be",
                  "here"
                ],
                "dotted.subkeys": [
                  "should be preserved",
                  {
                    "complex.weird.sub": {
                      "objects": true
                    },
                    "even.with": 1
                  }
                ],
                "valid": "JSON"
              }
            }
            """,
        ),
        Fuss(
            True,
            "my.json",
            SharedViolations.DIFFERENT_VALUES.code + JsonPlugin.violation_base_code,
            " has different values. Use this:",
            """
            {
              "formatting": {
                "on.the": "config file"
              }
            }
            """,
        ),
    ).assert_file_contents(
        "my.json", datadir / "3-expected.json"
    ).api_check_then_fix()


def test_invalid_json(tmp_path, datadir):
    """Test invalid JSON on a TOML style."""
    # pylint: disable=line-too-long
    ProjectMock(tmp_path).style(datadir / "4-style.toml").api_check_then_fix(
        Fuss(
            False,
            "nitpick-style.toml",
            1,
            " has an incorrect style. Invalid config:",
            f"""
            "another.json".contains_json.some_field.value: Invalid JSON (json.decoder.JSONDecodeError: Invalid control character at: line 1 column 37 (char 36))
            "another.json".with: Unknown configuration. See {READ_THE_DOCS_URL}nitpick_section.html.
            """,
        )
    )


def test_json_configuration(tmp_path):
    """Test configuration for JSON files."""
    ProjectMock(tmp_path).style(
        """
        ["your.json".has]
        an_extra = "key"

        ["their.json"]
        x = 1
        """
    ).api_check_then_fix(
        Fuss(
            False,
            "nitpick-style.toml",
            1,
            " has an incorrect style. Invalid config:",
            f"""
            "their.json".x: Unknown configuration. See {READ_THE_DOCS_URL}nitpick_section.html.
            "your.json".has: Unknown configuration. See {READ_THE_DOCS_URL}nitpick_section.html.
            """,
        )
    )


def test_jsonfile_deprecated(tmp_path):
    """Test configuration for JSON files."""
    with warnings.catch_warnings(record=True) as captured:
        # Cause all warnings to always be triggered.
        warnings.simplefilter("always")

        ProjectMock(tmp_path).style(
            """
            [nitpick.JSONFile]
            file_names = ["my.json"]

            ["my.json"]
            contains_keys = ["x"]
            """
        ).save_file("my.json", '{"x":1}').flake8().assert_no_errors()

        assert len(captured) == 1
        assert issubclass(captured[-1].category, DeprecationWarning)
        assert "The [nitpick.JSONFile] section is not needed anymore; just declare your JSON files directly" in str(
            captured[-1].message
        )
