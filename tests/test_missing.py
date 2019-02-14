"""Missing files tests."""
from flake8_nitpick import PyProjectTomlChecker
from tests.helpers import ProjectMock


def test_missing_pyproject_toml(request):
    """Suggest poetry init when pyproject.toml does not exist."""
    assert ProjectMock(request, pyproject_toml=False).lint().errors == {
        f"NIP201 {PyProjectTomlChecker.file_name} does not exist. Run 'poetry init' to create one."
    }


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
        """NIP331 File: .pre-commit-config.yaml: Missing file. Suggested initial content:
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
