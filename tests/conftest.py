"""Pytest configuration."""
import shutil
import tempfile
from pathlib import Path

import pytest

PROJECT_TEMP_ROOT_PATH = Path(tempfile.mkdtemp())


@pytest.yield_fixture("session", autouse=True)
def delete_project_temp_root():
    """Delete the project temp root after the tests have finished."""
    yield
    shutil.rmtree(str(PROJECT_TEMP_ROOT_PATH))
