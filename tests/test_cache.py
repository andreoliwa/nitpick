"""Test cache."""
import pytest
from freezegun import freeze_time


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


def test_default_cache_when_nothing_provided(project_remote):
    """Test the default cache option when nothing is provided: 1 hour."""
    with freeze_time("2021-03-16 11:00") as frozen_datetime:
        project_remote.assert_call_count(0)

        # One HTTP request
        project_remote.api_check().assert_violations().assert_call_count(1)

        # Still one request
        frozen_datetime.move_to("2021-03-16 11:30")
        project_remote.api_check().assert_violations().assert_call_count(1)

        # Time's up: another HTTP request
        frozen_datetime.move_to("2021-03-16 12:01")
        project_remote.api_check().assert_violations().assert_call_count(2)
