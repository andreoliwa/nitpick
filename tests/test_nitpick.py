"""Nitpick tests."""
from tests.helpers import ProjectMock


def test_no_root_dir():
    """Test a project with no root dir."""
    assert ProjectMock("no_root").lint().errors == ["NIP101 No root dir found (is this a Python project?)"]
