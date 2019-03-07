"""Pre-commit tests."""
from flake8_nitpick.files.pre_commit import PreCommitFile
from tests.helpers import ProjectMock


def test_pre_commit_should_be_deleted(request):
    """File should be deleted."""
    ProjectMock(request).style("").pre_commit("").lint().assert_errors_contain(
        f"NIP332 File {PreCommitFile.file_name} should be deleted"
    )


def test_missing_pre_commit_config_yaml(request):
    """Suggest initial contents for missing pre-commit config file."""
    ProjectMock(request).style(
        f'''
        [["{PreCommitFile.toml_key()}".repos]]
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
        f"""
        NIP331 File {PreCommitFile.file_name} was not found. Create it with this content:
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
        f"""
        ["{PreCommitFile.toml_key()}"]
        fail_fast = true
        whatever = "1"
        """
    ).lint().assert_errors_contain(
        f"""
        NIP331 File {PreCommitFile.file_name} was not found. Create it with this content:
        fail_fast: true
        whatever: '1'
        """
    )


def test_root_values_on_existing_file(request):
    """Test values on the root of the config file when there is a file."""
    ProjectMock(request).style(
        f"""
        ["{PreCommitFile.toml_key()}"]
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
        f"""
        NIP338 File {PreCommitFile.file_name} has missing values:
        blabla: what
        fail_fast: true
        """
    ).assert_errors_contain(
        f"""
        NIP339 File {PreCommitFile.file_name}: 'something' is False but it should be like this:
        something: true
        """
    )
