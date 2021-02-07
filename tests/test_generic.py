"""Generic functions tests."""
import sys
from pathlib import Path
from unittest import mock

import pytest

from nitpick.generic import MergeDict, get_subclasses, relative_to_cur_home_abs
from tests.helpers import assert_conditions


def test_get_subclasses():
    """Test subclasses."""

    # pylint: disable=missing-docstring,too-few-public-methods
    class Vehicle:
        pass

    class Car(Vehicle):
        pass

    class Audi(Car):
        pass

    class Bicycle(Vehicle):
        pass

    assert_conditions(get_subclasses(Vehicle) == [Car, Audi, Bicycle])


def test_merge_dicts_extending_lists():
    """Merge dictionaries extending lists."""
    merged = MergeDict({"parent": {"brother": 1, "sister": 2}})
    merged.add({"parent": {"other": 3}})
    assert_conditions(merged.merge() == {"parent": {"brother": 1, "sister": 2, "other": 3}})

    merged = MergeDict({"box": {"colors": ["blue", "yellow"], "cutlery": ("fork",)}})
    merged.add({"box": {"colors": ("white",), "cutlery": ["knife", "spoon"]}})
    assert_conditions(
        merged.merge() == {"box": {"colors": ["blue", "yellow", "white"], "cutlery": ["fork", "knife", "spoon"]}}
    )


@mock.patch.object(Path, "cwd")
@mock.patch.object(Path, "home")
@pytest.mark.xfail(condition=sys.platform == "win32", reason="Different path separator on Windows")
# TODO: fix Windows tests.
#  For this one, create a separate test mocking current and home folders on Windows. e.g: C:\\Users\\runneradmin\\
def test_relative_to_cur_home_full(home, cwd):
    """Mock the home and current dirs, and test relative paths to them (testing Linux-only)."""
    home_dir = "/home/john"
    project_dir = f"{home_dir}/project"

    home.return_value = Path(home_dir)
    cwd.return_value = Path(project_dir)
    for path, expected in {
        None: "",
        # Dirs
        project_dir: "",
        Path(project_dir): "",
        f"{home_dir}/another": "~/another",
        Path(f"{home_dir}/bla/bla"): "~/bla/bla",
        "/usr/bin/some": "/usr/bin/some",
        Path("/usr/bin/awesome"): "/usr/bin/awesome",
        # Files
        f"{project_dir}/tox.ini": "tox.ini",
        Path(f"{project_dir}/apps/manage.py"): "apps/manage.py",
        f"{home_dir}/another/one/bites/the/dust.py": "~/another/one/bites/the/dust.py",
        Path(f"{home_dir}/bla/bla.txt"): "~/bla/bla.txt",
        "/usr/bin/something/wicked/this-way-comes.cfg": "/usr/bin/something/wicked/this-way-comes.cfg",
        Path("/usr/bin/.awesome"): "/usr/bin/.awesome",
    }.items():
        assert relative_to_cur_home_abs(path) == expected
