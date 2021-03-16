"""Test cache."""
import pytest
from freezegun import freeze_time


# FIXME[AA]: test default cache
@pytest.mark.tool_nitpick("cache = 'forever'")
def test_forever(project_remote):
    """Test cache being stored forever."""
    project_remote.assert_call_count(0)
    for _ in range(3):
        project_remote.api_check().assert_violations()
    project_remote.assert_call_count(1)


@pytest.mark.tool_nitpick("cache = 'never'")
def test_never(project_remote):
    """Test cache being never stored."""
    project_remote.assert_call_count(0)
    for _ in range(3):
        project_remote.api_check().assert_violations()
    project_remote.assert_call_count(3)


@pytest.mark.tool_nitpick("cache = '15 minutes'")
def test_expiration(project_remote):
    """Test cache expiring after some time."""
    with freeze_time("2021-03-10 22:00") as frozen_datetime:
        project_remote.assert_call_count(0)

        # One HTTP request
        project_remote.api_check().assert_violations().assert_call_count(1)

        # Still one request
        frozen_datetime.move_to("2021-03-10 22:13")
        project_remote.api_check().assert_violations().assert_call_count(1)

        # Time's up: another HTTP request
        frozen_datetime.move_to("2021-03-10 22:16")
        project_remote.api_check().assert_violations().assert_call_count(2)
