"""Test GitHub workflows."""
from nitpick.violations import Fuss
from tests.helpers import ProjectMock


def test_steps_should_exist(tmp_path, datadir):
    """Test steps should exist."""
    filename = ".github/workflows/any-language.yaml"
    ProjectMock(tmp_path).save_file(filename, datadir / "steps-should-exist-actual.yaml").style(
        datadir / "steps-should-exist.toml"
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
        filename, datadir / "steps-should-exist-desired.yaml"
    ).api_check().assert_violations()
