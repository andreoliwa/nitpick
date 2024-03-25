"""Test GitHub workflows."""

from nitpick.violations import Fuss
from tests.helpers import ProjectMock


def test_list_of_dicts_search_missing_element_by_key_and_change_add_element_individually(tmp_path, datadir):
    """Test list of dicts: search missing element by key and change/add element individually.

    In GitHub Workflows: steps are searched by name and they should exist.
    """
    filename = ".github/workflows/any-language.yaml"
    ProjectMock(tmp_path).save_file(filename, datadir / "dict-search-by-key-actual.yaml").style(
        datadir / "dict-search-by-key-desired.toml"
    ).api_check_then_fix(
        Fuss(
            True,
            filename,
            368,
            " has missing values:",
            """
            jobs:
              build:
                steps:
                  - name: Checkout
                    uses: actions/checkout@v2
                  - name: Set up Python ${{ matrix.python-version }}
                    uses: actions/setup-python@v2
                    with:
                      python-version: ${{ matrix.python-version }}
                  - name: Install tox
                    run: python -m pip install tox
            """,
        ),
    ).assert_file_contents(
        filename, datadir / "dict-search-by-key-expected.yaml"
    ).api_check().assert_violations()


def test_list_of_scalars_only_add_elements_that_do_not_exist(tmp_path, datadir):
    """Test list of scalars: only add elements that do not exist.

    Only check if the element is present but don't enforce the whole list to be the same.
    """
    filename = ".github/workflows/python.yaml"
    ProjectMock(tmp_path).save_file(filename, datadir / "scalar-add-elements-that-do-not-exist-actual.yaml").style(
        datadir / "scalar-add-elements-that-do-not-exist-desired.toml"
    ).api_check_then_fix(
        Fuss(
            True,
            filename,
            368,
            " has missing values:",
            """
            jobs:
              build:
                strategy:
                  matrix:
                    os:
                      - ubuntu-latest
                    python-version:
                      - '3.10'
                      - '3.11'
                      - '3.12'
            """,
        ),
    ).assert_file_contents(
        filename, datadir / "scalar-add-elements-that-do-not-exist-expected.yaml"
    ).api_check().assert_violations()


def test_wildcard_expression_matches_multiple_keys(tmp_path, datadir):
    """Test wildcard expressions that match multiple keys.

    E.g.: any "jobs.*.steps".
    """
    filename = ".github/workflows/anything.yaml"
    ProjectMock(tmp_path).save_file(filename, datadir / "wildcard-actual.yaml").style(
        datadir / "wildcard-desired.toml"
    ).api_check_then_fix(
        Fuss(
            True,
            filename,
            368,
            " has missing values:",
            """
            jobs:
              build:
                steps:
                  - name: Checkout
                    uses: actions/checkout@v2
              test:
                steps:
                  - name: Checkout
                    uses: actions/checkout@v2
              release:
                steps:
                  - name: Checkout
                    uses: actions/checkout@v2
            """,
        ),
    ).assert_file_contents(
        filename, datadir / "wildcard-expected.yaml"
    ).api_check().assert_violations()


def test_steps_are_present_in_any_order(tmp_path, datadir):
    """Test steps are present in any order."""
    filename = ".github/workflows/any-order.yaml"
    ProjectMock(tmp_path).save_file(filename, datadir / "any-order.yaml").style(
        datadir / "any-order.toml"
    ).api_check_then_fix().assert_file_contents(filename, datadir / "any-order.yaml").api_check().assert_violations()


def test_more_than_one_element_with_the_same_key_only_first_one_will_be_considered(tmp_path, datadir):
    """Test more than one element with the same key: only the first one will be considered.

    E.g.: two steps with the same name.
    """
    filename = ".github/workflows/something.yaml"
    ProjectMock(tmp_path).save_file(filename, datadir / "same-key-actual.yaml").style(
        datadir / "same-key-desired.toml"
    ).api_check_then_fix(
        Fuss(
            True,
            filename,
            368,
            " has missing values:",
            """
            jobs:
              whatever:
                steps:
                  - name: Same key
                    uses: actions/replacing-duplicated-element@v2
            """,
        )
    ).assert_file_contents(
        filename, datadir / "same-key-expected.yaml"
    ).api_check().assert_violations()
