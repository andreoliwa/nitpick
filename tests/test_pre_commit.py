"""Pre-commit tests."""
from tests.helpers import ProjectMock


def test_missing_pre_commit_config_yaml(request):
    """Suggest initial contents for missing .pre-commit-config.yaml."""
    project = (
        ProjectMock(request)
        .style(
            '''
            [["pre-commit-config.yaml".repos]]
            repo = "local"
            hooks = """
            - id: whatever
              any: valid
              yaml: here
            - id: blargh
              note: only the id is verified
            """
            '''
        )
        .lint()
    )
    project.assert_errors_contain(
        """
        NIP331 File: .pre-commit-config.yaml: Missing file. Suggested initial content:
        repos:
        - hooks:
          - any: valid
            id: whatever
            yaml: here
          - id: blargh
            note: only the id is verified
          repo: local
        """
    )


def test_root_values_on_missing_file(request):
    """Test values on the root of the config file when it's missing."""
    project = (
        ProjectMock(request)
        .style(
            """
            ["pre-commit-config.yaml"]
            fail_fast = true
            whatever = "1"
            """
        )
        .lint()
    )
    project.assert_errors_contain(
        """
        NIP331 File: .pre-commit-config.yaml: Missing file. Suggested initial content:
        fail_fast: true
        whatever: '1'
        """
    )


def test_root_values_on_existing_file(request):
    """Test values on the root of the config file when there is a file."""
    project = (
        ProjectMock(request)
        .style(
            """
            ["pre-commit-config.yaml"]
            fail_fast = true
            blabla = "what"
            something = true
            """
        )
        .pre_commit(
            """
            repos:
            - hooks:
              - id: whatever
            something: false
            """
        )
        .lint()
    )
    project.assert_errors_contain(
        """
        NIP338 File: .pre-commit-config.yaml: Missing keys:
        blabla: what
        fail_fast: true
        """
    )
    project.assert_errors_contain(
        """
        NIP339 File: .pre-commit-config.yaml: Expected value True in key, got False
        something: true
        """
    )
