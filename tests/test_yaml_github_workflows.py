"""Test GitHub workflows."""
from nitpick.violations import Fuss
from tests.helpers import ProjectMock


def test_list_of_dicts_search_missing_element_by_key_and_change_add_element_individually(tmp_path, datadir):
    """Test list of dicts: search missing element by key and change/add element individually.

    In GitHub Workflows: steps are searched by name and they should exist.
    """
    filename = ".github/workflows/any-language.yaml"
    ProjectMock(tmp_path).save_file(filename, datadir / "dict-search-by-key-actual.yaml").style(
        datadir / "dict-search-by-key.toml"
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
        filename, datadir / "dict-search-by-key-desired.yaml"
    ).api_check().assert_violations()


def test_list_of_scalars_change_add_elements_starting_from_index_0_keep_remaining_items_if_they_exist(
    tmp_path, datadir
):
    """Test list of scalars: change/add elements starting from index 0, keep remaining items if they exist."""
    # FIXME List behaviour: Compare from first (dict or scalar) The current default for all lists... this should change
    filename = ".github/workflows/python.yaml"
    ProjectMock(tmp_path).save_file(filename, datadir / "scalar-change-from-index-zero-actual.yaml").style(
        datadir / "scalar-change-from-index-zero.toml"
    ).api_check_then_fix(
        Fuss(
            True,
            filename,
            369,
            " has different values. Use this:",
            """
            jobs:
              build:
                strategy:
                  matrix:
                    os:
                      - ubuntu-latest
                      - windows-latest
                    python-version:
                      - '3.7'
                      - '3.8'
                      - '3.9'
                      - '3.10'
                      - '3.11'
            """,
        ),
    ).assert_file_contents(
        filename, datadir / "scalar-change-from-index-zero-desired.yaml"
    ).api_check().assert_violations()


# FIXME: next: test a new step is added with the data if the style doesn't have the unique key (e.g. "name" for GHA)
