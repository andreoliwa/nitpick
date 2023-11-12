"""Test the tomlkit extensions."""
from pathlib import Path
from textwrap import dedent

import tomlkit

from nitpick import tomlkit_ext
from nitpick.tomlkit_ext import update_comment_before


def test_load_toml_from_io_or_path(shared_datadir: Path) -> None:
    """Load TOML from IO or path."""
    file = shared_datadir / "typed-style-dir/any/editorconfig.toml"
    from_io = tomlkit_ext.load(file.open("r"))
    from_path = tomlkit_ext.load(file)
    assert from_io == from_path


def assert_comment(
    before: str,
    after: str,
    *,
    table: str = "my.table",
    key: str = "simple-key",
    marker: str = "here",
    comment: str = "header\nfirst line",
) -> None:
    """Assert that the comment was updated as expected."""
    doc = tomlkit.parse(dedent(before))
    update_comment_before(doc[table], key, marker, comment)
    assert doc.as_string() == dedent(after)


def test_comment_between_existing_valid_markers() -> None:
    """Comment between existing valid markers."""
    assert_comment(
        """
        [my.table]
        # here-start
        # previous comment
        # here-end
        simple-key = "value"

        [another]
        x = 1
        """,
        """
        [my.table]
        # here-start one-line comment
        # here-end
        simple-key = "value"

        [another]
        x = 1
        """,
        comment="one-line comment",
    )


def test_missing_start_marker_but_valid_end_marker() -> None:
    """Missing start marker but valid end marker."""
    assert_comment(
        """
        [my.table]
        # previous comment
        # here-end
        simple-key = [1,2,
        3]


        [another]
        x = 2
        """,
        """
        [my.table]
        # here-start header
        # first line
        # here-end
        simple-key = [1,2,
        3]


        [another]
        x = 2
        """,
    )


def test_key_between_start_end_marker():
    """Another key between start/end marker."""
    assert_comment(
        """
        [my.table]
        # here-start header
        # open ended comment
        simple-key = [1,2,
        3]
        another-key = "value"
        [another.table]
        x = 2
        """,
        """
        [my.table]
        # here-start header
        # first line
        # here-end
        simple-key = [1,2,
        3]
        another-key = "value"
        [another.table]
        x = 2
        """,
    )


def test_missing_start_missing_end() -> None:
    """Missing start and missing end markers."""
    assert_comment(
        """
        [my.table]
        key-before = 3
        simple-key = "x"
        another-key = "value"
        [another.table]
        x = 2
        """,
        """
        [my.table]
        key-before = 3
        # here-start header
        # first line
        # here-end
        simple-key = "x"
        another-key = "value"
        [another.table]
        x = 2
        """,
    )


def test_valid_start_marker_but_missing_end():
    """Valid start marker but missing end."""
    assert_comment(
        """
        [my.table]
        # comment before
        # here-start header
        # open ended comment
        simple-key = 1
        another-key = "value"
        [another.table]
        x = 2
        """,
        """
        [my.table]
        # comment before
        # here-start header
        # first line
        # here-end
        simple-key = 1
        another-key = "value"
        [another.table]
        x = 2
        """,
    )


def test_multiple_end_markers() -> None:
    """Multiple end markers."""
    assert_comment(
        """
        [my.table]
        # before
        # here-start yeah
        # here-end one
        # here-end two
        # after
        simple-key = 1
        another-key = "value"
        [another.table]
        x = 2
        """,
        """
        [my.table]
        # before
        # here-start header
        # first line
        # here-end
        # after
        simple-key = 1
        another-key = "value"
        [another.table]
        x = 2
        """,
    )


def test_multiple_start_markers_first_one_is_used() -> None:
    """Multiple start markers, first one is used."""
    assert_comment(
        """
        [my.table]
        # before
        # here-start one
        # here-start two
        # here-end
        # after
        simple-key = 1
        another-key = "value"
        [another.table]
        x = 2
        """,
        """
        [my.table]
        # before
        # here-start header
        # first line
        # here-end
        # after
        simple-key = 1
        another-key = "value"
        [another.table]
        x = 2
        """,
    )


def test_searched_key_between_start_end_markers() -> None:
    """Searched key between start/end markers."""
    assert_comment(
        """
        [my.table]
        # before
        # here-start yeah
        # open ended comment
        # after
        simple-key = 123
        # here-end
        another-key = "value"
        [another.table]
        x = 2
        """,
        """
        [my.table]
        # before
        # here-start header
        # first line
        # here-end
        simple-key = 123
        # here-end
        another-key = "value"
        [another.table]
        x = 2
        """,
    )


def test_updating_a_comment_before_a_key_that_doesnt_exist() -> None:
    """Updating a comment before a key that doesn't exist."""
    assert_comment(
        """
        [my.table]
        # before
        # open ended comment
        # after
        another-key = "value"
        [another.table]
        x = 2
        """,
        """
        [my.table]
        # before
        # open ended comment
        # after
        another-key = "value"
        # here-start header
        # first line
        # here-end
        [another.table]
        x = 2
        """,
        key="some-other-key",
    )


def test_empty_comment_nothing_changes() -> None:
    """Empty comment."""
    content = """
        [my.table]
        # before
        # here-start header
        # existing comment
        # here-end
        # after
        another-key = "value"
        [another.table]
        x = 2
        """
    assert_comment(content, content, comment="")
