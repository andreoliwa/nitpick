"""JSON tests."""
import warnings

import pytest

from nitpick.constants import PACKAGE_JSON, READ_THE_DOCS_URL
from nitpick.plugins.json import JSONPlugin
from nitpick.violations import Fuss, SharedViolations
from tests.helpers import ProjectMock

# FIXME: use pytest-datafiles
PACKAGE_JSON_STYLE = '''
    ["package.json"]
    contains_keys = ["name", "version", "repository.type", "repository.url", "release.plugins"]

    ["package.json".contains_json]
    commitlint = """
      {
        "extends": [
          "@commitlint/config-conventional"
        ]
      }
    """
'''


def test_suggest_initial_contents(tmp_path):
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
    ProjectMock(tmp_path).named_style("package-json", PACKAGE_JSON_STYLE).pyproject_toml(
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


def test_json_file_contains_keys_mixed_with_contains_json_content(tmp_path):
    """Test if JSON file contains keys, mixed with "contains_json" content."""
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
    ProjectMock(tmp_path).named_style("package-json", PACKAGE_JSON_STYLE).pyproject_toml(
        """
        [tool.nitpick]
        style = ["package-json"]
        """
    ).save_file(PACKAGE_JSON, '{"name": "myproject", "version": "0.0.1", "something": "else"}').api_check_then_fix(
        Fuss(
            True,
            PACKAGE_JSON,
            SharedViolations.MISSING_VALUES.code + JSONPlugin.violation_base_code,
            " has missing values:",
            """
            {
              "commitlint": {
                "extends": [
                  "@commitlint/config-conventional"
                ]
              },
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
    ).assert_file_contents(
        PACKAGE_JSON, expected_package_json
    )


@pytest.mark.xfail(reason="Fixing one test at a time")
def test_missing_different_values(tmp_path):
    """Test missing and different values on the JSON file."""
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
            348,
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
            349,
            " has different values. Use this:",
            """
            {
              "formatting": {
                "on.the": "config file"
              }
            }
            """,
        ),
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
