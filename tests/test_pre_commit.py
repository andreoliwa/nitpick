"""Pre-commit tests."""
from tests.helpers import ProjectMock


def test_missing_pre_commit_config_yaml(request):
    """Suggest initial contents for missing .pre-commit-config.yaml."""
    ProjectMock(request).style(
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
    ).lint().assert_errors_contain(
        """
        NIP331 File .pre-commit-config.yaml was not found. Create it with this content:
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
    ProjectMock(request).style(
        """
        ["pre-commit-config.yaml"]
        fail_fast = true
        whatever = "1"
        """
    ).lint().assert_errors_contain(
        """
        NIP331 File .pre-commit-config.yaml was not found. Create it with this content:
        fail_fast: true
        whatever: '1'
        """
    )


def test_root_values_on_existing_file(request):
    """Test values on the root of the config file when there is a file."""
    ProjectMock(request).style(
        """
        ["pre-commit-config.yaml"]
        fail_fast = true
        blabla = "what"
        something = true
        """
    ).pre_commit(
        """
        repos:
        - hooks:
          - id: whatever
        something: false
        """
    ).lint().assert_errors_contain(
        """
        NIP338 File .pre-commit-config.yaml has missing values:
        blabla: what
        fail_fast: true
        """
    ).assert_errors_contain(
        """
        NIP339 File .pre-commit-config.yaml: 'something' is False but it should be like this:
        something: true
        """
    )
