"""Generic functions tests."""
from pathlib import Path
from unittest import mock

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


@mock.patch.object(Path, "cwd", return_value=Path("/home/john/project"))
@mock.patch.object(Path, "home", return_value=Path("/home/john"))
def test_relative_to_cur_home_full(home, cwd):
    """Mock the home and current dirs, and test relative paths to them."""
    for path, expected in {
        None: "",
        # Dirs
        "/home/john/project": "",
        Path("/home/john/project"): "",
        "/home/john/another": "~/another",
        Path("/home/john/bla/bla"): "~/bla/bla",
        "/usr/bin/some": "/usr/bin/some",
        Path("/usr/bin/awesome"): "/usr/bin/awesome",
        # Files
        "/home/john/project/tox.ini": "tox.ini",
        Path("/home/john/project/apps/manage.py"): "apps/manage.py",
        "/home/john/another/one/bites/the/dust.py": "~/another/one/bites/the/dust.py",
        Path("/home/john/bla/bla.txt"): "~/bla/bla.txt",
        "/usr/bin/something/wicked/this-way-comes.cfg": "/usr/bin/something/wicked/this-way-comes.cfg",
        Path("/usr/bin/.awesome"): "/usr/bin/.awesome",
    }.items():
        assert relative_to_cur_home_abs(path) == expected
