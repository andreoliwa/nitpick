# -*- coding: utf-8 -*-
"""Pre-commit tests."""
from tests.helpers import ProjectMock


def test_pre_commit_should_be_deleted(request):
    """File should be deleted."""
    ProjectMock(request).style("").pre_commit("").lint().assert_errors_contain(
        "NIP332 File .pre-commit-config.yaml should be deleted"
    )


def test_missing_pre_commit_config_yaml(request):
    """Suggest initial contents for missing pre-commit config file."""
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
        another_thing = "yep"
        """
    ).pre_commit(
        """
        repos:
        - hooks:
          - id: whatever
        something: false
        another_thing: "nope"
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
    ).assert_errors_contain(
        """
        NIP339 File .pre-commit-config.yaml: 'another_thing' is 'nope' but it should be like this:
        another_thing: yep
        """
    )


def test_missing_repos(request):
    """Test missing repos on file."""
    ProjectMock(request).style(
        """
        ["pre-commit-config.yaml"]
        fail_fast = true
        """
    ).pre_commit(
        """
        grepos:
        - hooks:
          - id: whatever
        """
    ).lint().assert_errors_contain(
        "NIP331 File .pre-commit-config.yaml doesn't have the 'repos' root key"
    )


def test_missing_repo_key(request):
    """Test missing repo key on the style file."""
    ProjectMock(request).style(
        """
        [["pre-commit-config.yaml".repos]]
        grepo = "glocal"
        """
    ).pre_commit(
        """
        repos:
        - hooks:
          - id: whatever
        """
    ).lint().assert_single_error(
        "NIP332 File .pre-commit-config.yaml: style file is missing 'repo' key in repo #0"
    )


def test_repo_does_not_exist(request):
    """Test repo does not exist on the pre-commit file."""
    ProjectMock(request).style(
        """
        [["pre-commit-config.yaml".repos]]
        repo = "local"
        """
    ).pre_commit(
        """
        repos:
        - hooks:
          - id: whatever
        """
    ).lint().assert_single_error(
        "NIP333 File .pre-commit-config.yaml: repo 'local' does not exist under 'repos'"
    )


def test_missing_hooks_in_repo(request):
    """Test missing hooks in repo."""
    ProjectMock(request).style(
        """
        [["pre-commit-config.yaml".repos]]
        repo = "whatever"
        """
    ).pre_commit(
        """
        repos:
        - repo: whatever
        """
    ).lint().assert_single_error(
        "NIP334 File .pre-commit-config.yaml: missing 'hooks' in repo 'whatever'"
    )


def test_style_missing_hooks_in_repo(request):
    """Test style file is missing hooks in repo."""
    ProjectMock(request).style(
        """
        [["pre-commit-config.yaml".repos]]
        repo = "another"
        """
    ).pre_commit(
        """
        repos:
        - repo: another
          hooks:
          - id: isort
        """
    ).lint().assert_single_error(
        "NIP335 File .pre-commit-config.yaml: style file is missing 'hooks' in repo 'another'"
    )


def test_style_missing_id_in_hook(request):
    """Test style file is missing id in hook."""
    ProjectMock(request).style(
        '''
        [["pre-commit-config.yaml".repos]]
        repo = "another"
        hooks = """
        - name: isort
          entry: isort -sp setup.cfg
        """
        '''
    ).pre_commit(
        """
        repos:
        - repo: another
          hooks:
          - id: isort
        """
    ).lint().assert_single_error(
        """
        NIP336 File .pre-commit-config.yaml: style file is missing 'id' in hook:
            entry: isort -sp setup.cfg
            name: isort
        """
    )


def test_missing_hook_with_id(request):
    """Test missing hook with specific id."""
    ProjectMock(request).style(
        '''
        [["pre-commit-config.yaml".repos]]
        repo = "other"
        hooks = """
        - id: black
          name: black
          entry: black
        """
        '''
    ).pre_commit(
        """
        repos:
        - repo: other
          hooks:
          - id: isort
        """
    ).lint().assert_single_error(
        """
        NIP337 File .pre-commit-config.yaml: missing hook with id 'black':
          - id: black
            entry: black
            name: black
        """
    )
