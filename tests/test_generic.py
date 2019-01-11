"""Generic functions tests."""
from flake8_nitpick.generic import find_object_by_key, flatten, get_subclasses, unflatten


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

    assert get_subclasses(Vehicle) == [Car, Audi, Bicycle]


def test_flatten():
    """Test flattening a nested dict."""
    assert flatten({"root": {"sub1": 1, "sub2": {"deep": 3}}, "sibling": False}) == {
        "root.sub1": 1,
        "root.sub2.deep": 3,
        "sibling": False,
    }


def test_unflatten():
    """Test unflattening a dict."""
    assert unflatten({"my.sub.path": True, "another.path": 3, "my.home": 4}) == {
        "my": {"sub": {"path": True}, "home": 4},
        "another": {"path": 3},
    }


def test_find_object_by_key():
    """Test finding an object in a list."""
    banana = {"id": 1, "fruit": "banana"}
    fruits = [banana, {"id": 2, "fruit": "apple"}, {"id": 3, "fruit": "mango"}]
    assert find_object_by_key(fruits, "id", 1) == banana
    assert find_object_by_key(fruits, "fruit", "banana") == banana
    assert find_object_by_key(fruits, "fruit", "pear") == {}
