"""Violations."""
from textwrap import dedent

import pytest
from marshmallow import ValidationError
from testfixtures import compare

from nitpick.constants import EmojiEnum
from nitpick.schemas import flatten_marshmallow_errors
from nitpick.violations import Fuss, Reporter
from tests.helpers import SUGGESTION_BEGIN, SUGGESTION_END


@pytest.mark.parametrize("fixed", [False, True])
def test_fuss_pretty(fixed):
    """Test Fuss' pretty formatting."""
    examples = [
        (Fuss(fixed, "abc.txt", 2, "message"), "abc.txt:1: NIP002 message"),
        (Fuss(fixed, "abc.txt", 2, "message", "", 15), "abc.txt:15: NIP002 message"),
        (
            Fuss(fixed, "abc.txt", 1, "message", "\tsuggestion\n\t   "),
            f"abc.txt:1: NIP001 message{SUGGESTION_BEGIN}\n\tsuggestion{SUGGESTION_END}",
        ),
        (Fuss(fixed, "  ", 3, "no filename"), "NIP003 no filename"),
    ]
    for fuss, expected in examples:
        compare(actual=fuss.pretty, expected=dedent(expected))


def test_reporter():
    """Test error reporter."""
    reporter = Reporter()
    reporter.reset()
    assert reporter.manual == 0
    assert reporter.fixed == 0
    assert reporter.get_counts() == f"No violations found. {EmojiEnum.STAR_CAKE.value}"

    reporter.increment()
    assert reporter.manual == 1
    assert reporter.fixed == 0
    assert reporter.get_counts() == f"Violations: {EmojiEnum.X_RED_CROSS.value} 1 to fix manually."

    reporter.increment(True)
    assert reporter.manual == 1
    assert reporter.fixed == 1
    assert (
        reporter.get_counts()
        == f"Violations: {EmojiEnum.GREEN_CHECK.value} 1 fixed, {EmojiEnum.X_RED_CROSS.value} 1 to fix manually."
    )

    reporter.reset()
    assert reporter.manual == 0
    assert reporter.fixed == 0

    reporter.increment(True)
    assert reporter.manual == 0
    assert reporter.fixed == 1
    assert reporter.get_counts() == f"Violations: {EmojiEnum.GREEN_CHECK.value} 1 fixed."


def test_flatten_marshmallow_errors():
    """Flatten Marshmallow errors."""
    examples = [
        ({"list": ["multi", "part", "message"]}, "list: multi, part, message"),
        ({"dict": {"a": "blargh", "b": "blergh"}}, "dict.a: blargh\ndict.b: blergh"),
        ({"dict": {"a": ["x", "y"], "b": "blergh"}}, "dict.a: x, y\ndict.b: blergh"),
        ({"tuple": ("c", "meh")}, "tuple: c, meh"),
        ({"err": ValidationError("some error")}, "err: some error"),
    ]
    for error, expected in examples:
        compare(actual=flatten_marshmallow_errors(error), expected=expected)
