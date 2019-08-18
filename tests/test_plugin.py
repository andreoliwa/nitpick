"""Plugin tests."""
from tests.helpers import ProjectMock


def test_absent_files(request):
    """Test absent files from the style configuration."""
    ProjectMock(request).style(
        """
        [nitpick.files.absent]
        xxx = "Remove this"
        yyy = "Remove that"
        """
    ).touch_file("xxx").touch_file("yyy").lint().assert_errors_contain(
        "NIP104 File xxx should be deleted: Remove this"
    ).assert_errors_contain(
        "NIP104 File yyy should be deleted: Remove that"
    )


def test_files_beginning_with_dot(request):
    """Test files beginning with a dot: the can't be used on [nitpick.files] (for now)."""
    ProjectMock(request).style(
        """
        [nitpick.files.".editorconfig"]
        missing_message = "Create this file"
        """
    ).lint().assert_errors_contain(
        """
        NIP001 File nitpick-style.toml has an incorrect style. Invalid TOML:\x1b[92m
        TomlDecodeError: Invalid group name \'editorconfig"\'. Try quoting it. (line 1 column 1 char 0)\x1b[0m
        """
    )


def test_present_files(request):
    """Test present files from the style configuration."""
    ProjectMock(request).style(
        """
        [nitpick.files.present]
        ".editorconfig" = "Create this file"
        ".env" = ""
        "another-file.txt" = ""
        """
    ).lint().assert_errors_contain("NIP103 File .editorconfig should exist: Create this file").assert_errors_contain(
        "NIP103 File .env should exist"
    ).assert_errors_contain(
        "NIP103 File another-file.txt should exist", 3
    )
