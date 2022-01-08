"""Test blender of dicts and related functions."""
import pytest
from testfixtures import compare

from nitpick.blender import DictBlender
from nitpick.constants import DOT
from tests.helpers import assert_conditions


def test_flatten():
    """Test the flatten function with variations."""
    examples = [
        (
            {"root": {"sub1": 1, "sub2": {"deep": 3}}, "sibling": False},
            {"root.sub1": 1, "root.sub2.deep": 3, "sibling": False},
            ".",
        ),
        (
            {"parent": {"with.dot": {"again": True}, "my.my": 1, 123: "numeric-key"}},
            {'parent."with.dot".again': True, 'parent."my.my"': 1, "parent.123": "numeric-key"},
            ".",
        ),
        (
            {
                "parent": {
                    "my#my": ("inner", "tuple", "turns", "to", "list"),
                    "with#hash": {"inner_list": ["x", "y", "z"]},
                }
            },
            {
                'parent#"my#my"': ["inner", "tuple", "turns", "to", "list"],
                'parent#"with#hash"#inner_list': ["x", "y", "z"],
            },
            "#",
        ),
    ]
    for original, expected, separator in examples:
        compare(actual=DictBlender(original, separator=separator).flat_dict, expected=expected)


def test_merge_dicts_extending_lists():
    """Merge dictionaries extending lists."""
    blender = DictBlender({"parent": {"brother": 1, "sister": 2}})
    blender.add({"parent": {"other": 3}})
    assert_conditions(blender.mix() == {"parent": {"brother": 1, "sister": 2, "other": 3}})

    blender = DictBlender({"box": {"colors": ["blue", "yellow"], "cutlery": ("fork",)}})
    blender.add({"box": {"colors": ("white",), "cutlery": ["knife", "spoon"]}})
    assert_conditions(
        blender.mix() == {"box": {"colors": ["blue", "yellow", "white"], "cutlery": ["fork", "knife", "spoon"]}}
    )


def test_unflatten_valid():
    """Valid dict being unflattened."""
    blender = DictBlender({"my.sub.path": True, "another.path": 3, "my.home": 4}, separator=DOT, flatten_on_add=False)
    assert blender.mix() == {"my": {"sub": {"path": True}, "home": 4}, "another": {"path": 3}}


def test_unflatten_invalid():
    """Invalid dict being unflattened."""
    blender = DictBlender(
        {"repo": "conflicted key", "repo.name": "?", "repo.path": "?"}, separator=DOT, flatten_on_add=False
    )
    with pytest.raises(TypeError) as err:
        blender.mix()
    assert "'str' object does not support item assignment" in str(err)
