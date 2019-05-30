# -*- coding: utf-8 -*-
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
        "NIP103 File xxx should be deleted: Remove this"
    ).assert_errors_contain(
        "NIP103 File yyy should be deleted: Remove that"
    )
