"""Test the tomlkit extensions."""
from textwrap import dedent

import tomlkit

from nitpick.tomlkit_ext import update_comment_before


def assert_comment(table: str, key: str, marker: str, comment: str, before: str, after: str) -> None:
    """Assert that the comment was updated as expected."""
    doc = tomlkit.parse(dedent(before))
    update_comment_before(doc[table], key, marker, comment)
    assert doc.as_string() == dedent(after)


def test_comment_between_existing_valid_markers() -> None:
    """Comment between existing valid markers."""
    assert_comment(
        "my.table",
        "my-key",
        "yeah",
        "one-line comment",
        """
        [my.table]
        # yeah-start
        # previous comment
        # yeah-end
        my-key = "value"

        [another]
        x = 1
        """,
        """
        [my.table]
        # yeah-start one-line comment
        # yeah-end
        my-key = "value"

        [another]
        x = 1
        """,
    )


def test_missing_start_marker_but_valid_end_marker() -> None:
    """Missing start marker but valid end marker."""
    assert_comment(
        "my.deeper.table",
        "simple-key",
        "here",
        "header\nfirst line",
        """
        [my.deeper.table]
        # here-end
        simple-key = [1,2,
        3]


        [another]
        x = 2
        """,
        """
        [my.deeper.table]
        # here-start header
        # first line
        # here-end
        simple-key = [1,2,
        3]


        [another]
        x = 2
        """,
    )


def test_another_key_between_start_end_marker():
    """Another key between start/end marker."""
    assert_comment(
        "my.deeper.table",
        "simple-key",
        "here",
        "header\nfirst line",
        """
        [my.deeper.table]
        # here-start header
        # open ended comment
        simple-key = [1,2,
        3]
        another-key = "value"
        # here-end
        [another.table]
        x = 2
        """,
        """
        [my.deeper.table]
        # here-start header
        # first line
        # here-end
        simple-key = [1,2,
        3]
        another-key = "value"
        # here-end
        [another.table]
        x = 2
        """,
    )


# TODO(AA): test: valid start/missing end
# TODO(AA): test: missing start/missing end
# TODO(AA): test: multiple start
# TODO(AA): test: multiple end
# TODO(AA): test: searched key between start/end

# TODO(AA): test: updating a comment before a key that doesn't exist
