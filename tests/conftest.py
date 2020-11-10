"""Pytest configuration."""
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# If the env variable is set, use it as the temporary root; this helps local debugging.
NITPICK_TEST_DIR = os.environ.get("NITPICK_TEST_DIR")

# Otherwise, a temporary root will be used.
_ROOT = NITPICK_TEST_DIR or tempfile.mkdtemp()
if sys.platform == "darwin" and not _ROOT.startswith("/private"):
    # On macOS, use /private/<temp dir> as the root instead of /<temp dir>, otherwise lots of tests will fail.
    _ROOT = "/private" + _ROOT

TEMP_PATH = Path(_ROOT).expanduser().absolute()


@pytest.fixture(scope="session", autouse=True)
def delete_project_temp_root():
    """Delete the temporary root before or after running the tests, depending on the env variable."""
    if NITPICK_TEST_DIR:
        # If the environment variable is configured, delete its contents before the tests.
        if TEMP_PATH.exists():
            shutil.rmtree(str(TEMP_PATH))
        TEMP_PATH.mkdir()

    yield

    if not NITPICK_TEST_DIR:
        # If the environment variable is not configured, then a random temp dir will be used;
        # its contents should be deleted after the tests.
        shutil.rmtree(str(TEMP_PATH))
