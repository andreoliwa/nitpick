"""Generic functions tests."""
from nitpick.generic import MergeDict, get_subclasses
from tests.helpers import assert_conditions


def test_get_subclasses():
    """Test subclasses."""

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
    md = MergeDict({"parent": {"brother": 1, "sister": 2}})
    md.add({"parent": {"other": 3}})
    assert_conditions(md.merge() == {"parent": {"brother": 1, "sister": 2, "other": 3}})

    md = MergeDict({"box": {"colors": ["blue", "yellow"], "cutlery": ("fork",)}})
    md.add({"box": {"colors": ("white",), "cutlery": ["knife", "spoon"]}})
    assert_conditions(
        md.merge() == {"box": {"colors": ["blue", "yellow", "white"], "cutlery": ["fork", "knife", "spoon"]}}
    )
