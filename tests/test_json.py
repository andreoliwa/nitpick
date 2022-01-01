"""JSON tests."""
import warnings

import pytest

from nitpick.constants import PACKAGE_JSON, READ_THE_DOCS_URL
from nitpick.plugins.json import JsonPlugin
from nitpick.violations import Fuss, SharedViolations
from tests.helpers import ProjectMock


@pytest.fixture()
def package_json_style(shared_datadir) -> str:
    """A sample style for package.json."""
    return (shared_datadir / "sample-package-json-style.toml").read_text()


# FIXME: use datadir
def test_suggest_initial_contents(tmp_path, package_json_style):
    """Suggest initial contents for missing JSON file."""
    expected_package_json = """
        {
          "commitlint": {
            "extends": [
              "@commitlint/config-conventional"
            ]
          },
          "name": "<some value here>",
          "release": {
            "plugins": "<some value here>"
          },
          "repository": {
            "type": "<some value here>",
            "url": "<some value here>"
          },
          "version": "<some value here>"
        }
    """
    ProjectMock(tmp_path).named_style("package-json", package_json_style).pyproject_toml(
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
    )


def test_missing_different_values_with_contains_json_with_contains_keys(tmp_path, package_json_style):
    """Test missing and different values with "contains_json" and "contains_keys"."""
    expected_package_json = """
        {
          "commitlint": {
            "extends": [
              "@commitlint/config-conventional"
            ]
          },
          "name": "myproject",
          "release": {
            "plugins": "<some value here>"
          },
          "repository": {
            "type": "<some value here>",
            "url": "<some value here>"
          },
          "something": "else",
          "version": "0.0.1"
        }
    """
    ProjectMock(tmp_path).named_style("package-json", package_json_style).pyproject_toml(
        """
        [tool.nitpick]
        style = ["package-json"]
        """
    ).save_file(
        PACKAGE_JSON,
        """
        {
          "name": "myproject",
          "version": "0.0.1",
          "something": "else",
          "commitlint":{"extends":["wrong-plugin-should-be-replaced","another-wrong-plugin"]}
        }
        """,
    ).api_check_then_fix(
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
            SharedViolations.DIFFERENT_VALUES.code + JsonPlugin.violation_base_code,
            " has different values. Use this:",
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
    )


def test_missing_different_values_with_contains_json_without_contains_keys(tmp_path):
    """Test missing and different values with "contains_json", without "contains_keys"."""
    ProjectMock(tmp_path).style(
        '''
        ["my.json".contains_json]
        "some.dotted.root.key" = """
            { "valid": "JSON", "content": ["should", "be", "here"]  , "dotted.subkeys"  : ["should be preserved",
            {"even.with": 1, "complex.weird.sub":{"objects":true}}] }
        """
        formatting = """ {"doesnt":"matter","here":true,"on.the": "config file"} """
        '''
    ).save_file("my.json", '{"name":"myproject","formatting":{"on.the":"actual file"}}').api_check_then_fix(
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
        "my.json",
        """
        {
          "formatting": {
            "doesnt": "matter",
            "here": true,
            "on.the": "config file"
          },
          "name": "myproject",
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
    )


def test_invalid_json(tmp_path):
    """Test invalid JSON on a TOML style."""
    # pylint: disable=line-too-long
    ProjectMock(tmp_path).style(
        '''
        ["another.json".contains_json]
        some_field = """
            { "this": "is missing the end...
        """

        ["another.json".with]
        extra = "key"
        '''
    ).api_check_then_fix(
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
