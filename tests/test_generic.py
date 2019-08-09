"""Generic functions tests."""
from nitpick.generic import MergeDict, get_subclasses
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
