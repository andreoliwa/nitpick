"""Tests for the deprecated ``nitpick.plugins.pre_commit.PreCommitPlugin`` with the old style format.

.. warning::

    Read the warning on :py:class:`nitpick.plugins.yaml.YamlPlugin`.
"""
import warnings

import pytest

from nitpick.constants import PRE_COMMIT_CONFIG_YAML, SETUP_CFG
from nitpick.violations import Fuss
from tests.helpers import ProjectMock, filter_desired_warning


def test_pre_commit_has_no_configuration(tmp_path):
    """No errors should be raised if pre-commit is not referenced in any style file.

    Also the file should not be deleted unless explicitly asked.
    """
    ProjectMock(tmp_path).style("").pre_commit("").api_check_then_fix()


def test_pre_commit_referenced_in_style(tmp_path):
    """Only check files if they have configured styles."""
    ProjectMock(tmp_path).style(
        """
        [".pre-commit-config.yaml"]
        fail_fast = true
        """
    ).pre_commit("").api_check_then_fix(
        Fuss(True, PRE_COMMIT_CONFIG_YAML, 368, " has missing values:", "fail_fast: true")
    )


def test_suggest_initial_contents(tmp_path, datadir):
    """Suggest initial contents for missing pre-commit config file."""
    warnings.simplefilter("ignore")  # "repos.yaml" key
    ProjectMock(tmp_path).named_style("isort", datadir / "1-isort.toml").named_style(
        "black", datadir / "1-black.toml"
    ).pyproject_toml(
        """
        [tool.nitpick]
        style = ["isort", "black"]
        """
    ).api_check_then_fix(
        Fuss(
            True,
            PRE_COMMIT_CONFIG_YAML,
            361,
            " was not found. Create it with this content:",
            """
            repos: []
            """,
        ),
        partial_names=[PRE_COMMIT_CONFIG_YAML],
    ).assert_file_contents(
        PRE_COMMIT_CONFIG_YAML,
        """
        repos: []
        """,
    )


def test_no_yaml_key(tmp_path):
    """What was an invalid repo config before, now will be autofixed.

    Read the warning on :py:class:`nitpick.plugins.yaml.YamlPlugin`.
    """
    ProjectMock(tmp_path).style(
        '''
        [[".pre-commit-config.yaml".repos]]
        missing_yaml_key = """
          - repo: https://github.com/PyCQA/isort
            rev: 5.8.0
            hooks:
              - id: isort
        """
        '''
    ).api_check_then_fix(
        Fuss(
            True,
            PRE_COMMIT_CONFIG_YAML,
            361,
            " was not found. Create it with this content:",
            "repos:\n"
            '  - missing_yaml_key: "  - repo: '
            "https://github.com/PyCQA/isort\\n    rev: 5.8.0\\n\\\n"
            '      \\    hooks:\\n      - id: isort\\n"',
        )
    )


def test_root_values_on_missing_file(tmp_path):
    """Test values on the root of the config file when it's missing."""
    ProjectMock(tmp_path).style(
        """
        [".pre-commit-config.yaml"]
        bla_bla = "oh yeah"
        fail_fast = true
        whatever = "1"
        """
    ).api_check_then_fix(
        Fuss(
            True,
            PRE_COMMIT_CONFIG_YAML,
            361,
            " was not found. Create it with this content:",
            """
            bla_bla: oh yeah
            fail_fast: true
            whatever: '1'
            """,
        )
    )


def test_root_values_on_existing_file(tmp_path):
    """Test values on the root of the config file when there is a file."""
    ProjectMock(tmp_path).style(
        """
        [".pre-commit-config.yaml"]
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
    ).api_check_then_fix(
        Fuss(
            True,
            PRE_COMMIT_CONFIG_YAML,
            368,
            " has missing values:",
            """
            fail_fast: true
            blabla: what
            """,
        ),
        Fuss(
            True,
            PRE_COMMIT_CONFIG_YAML,
            369,
            " has different values. Use this:",
            """
            something: true
            another_thing: yep
            """,
        ),
    )


def test_missing_repos(tmp_path):
    """Test missing repos on file."""
    ProjectMock(tmp_path).style(
        """
        [".pre-commit-config.yaml"]
        fail_fast = true
        """
    ).pre_commit(
        """
        grepos:
        - hooks:
          - id: whatever
        """
    ).api_check_then_fix(
        Fuss(True, PRE_COMMIT_CONFIG_YAML, 368, " has missing values:", "fail_fast: true")
    )


def test_missing_repo_key(tmp_path):
    """Test missing repo key on the style file."""
    ProjectMock(tmp_path).style(
        """
        [[".pre-commit-config.yaml".repos]]
        grepo = "glocal"
        """
    ).pre_commit(
        """
        repos:
        - hooks:
          - id: whatever
        """
    ).api_check_then_fix(
        Fuss(
            True,
            PRE_COMMIT_CONFIG_YAML,
            368,
            " has missing values:",
            """
            repos:
              - grepo: glocal
            """,
        ),
    ).assert_file_contents(
        PRE_COMMIT_CONFIG_YAML,
        """
        repos:
          - hooks:
              - id: whatever
          - grepo: glocal
        """,
    )


def test_repo_does_not_exist(tmp_path):
    """Test repo does not exist on the pre-commit file."""
    ProjectMock(tmp_path).style(
        """
        [[".pre-commit-config.yaml".repos]]
        repo = "local"
        """
    ).pre_commit(
        """
        repos:
        - hooks:
          - id: whatever
        """
    ).api_check_then_fix(
        Fuss(
            True,
            PRE_COMMIT_CONFIG_YAML,
            368,
            " has missing values:",
            """
            repos:
              - repo: local
            """,
        )
    )


def test_missing_hooks_in_repo(tmp_path):
    """Test missing hooks in repo.

    Read the warning on :py:class:`nitpick.plugins.yaml.YamlPlugin`.
    """
    ProjectMock(tmp_path).style(
        """
        [[".pre-commit-config.yaml".repos]]
        repo = "whatever"
        """
    ).pre_commit(
        """
        repos:
        - repo: whatever
        """
    ).api_check_then_fix()


def test_style_missing_hooks_in_repo(tmp_path):
    """Test style file is missing hooks in repo."""
    ProjectMock(tmp_path).style(
        """
        [[".pre-commit-config.yaml".repos]]
        repo = "another"
        """
    ).pre_commit(
        """
        repos:
        - repo: another
          hooks:
          - id: isort
        """
    ).api_check_then_fix(
        Fuss(
            True,
            PRE_COMMIT_CONFIG_YAML,
            368,
            " has missing values:",
            """
            repos:
              - repo: another
            """,
        )
    )


def test_style_missing_id_in_hook(tmp_path):
    """Test style file is missing id in hook.

    Read the warning on :py:class:`nitpick.plugins.yaml.YamlPlugin`.
    """
    ProjectMock(tmp_path).style(
        f'''
        [[".pre-commit-config.yaml".repos]]
        repo = "another"
        hooks = """
        - name: isort
          entry: isort -sp {SETUP_CFG}
        """
        '''
    ).pre_commit(
        """
        repos:
        - repo: another
          hooks:
          - id: isort
        """
    ).api_check_then_fix(
        Fuss(
            True,
            PRE_COMMIT_CONFIG_YAML,
            368,
            " has missing values:",
            'repos:\n  - repo: another\n    hooks: "- name: isort\\n  entry: isort -sp setup.cfg\\n"',
        )
    ).assert_file_contents(
        PRE_COMMIT_CONFIG_YAML,
        r"""
        repos:
          - repo: another
            hooks:
              - id: isort
          - repo: another
            hooks: "- name: isort\n  entry: isort -sp setup.cfg\n"
        """,
    )


def test_missing_hook_with_id(tmp_path):
    """Test missing hook with specific id."""
    ProjectMock(tmp_path).style(
        '''
        [[".pre-commit-config.yaml".repos]]
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
    ).api_check_then_fix(
        Fuss(
            True,
            PRE_COMMIT_CONFIG_YAML,
            368,
            " has missing values:",
            """
            repos:
              - repo: other
                hooks: "- id: black\\n  name: black\\n  entry: black\\n"
            """,
        )
    )


def test_missing_different_values(tmp_path, datadir, shared_datadir):
    """Test missing and different values on the hooks.

    All "yaml" keys in the style are now ignored.

    Read the warning on :py:class:`nitpick.plugins.yaml.YamlPlugin`.
    """
    warnings.simplefilter("ignore")  # "repos.yaml" key
    ProjectMock(tmp_path).named_style(
        "root", shared_datadir / "pre-commit-config-with-old-repos-yaml-key.toml"
    ).named_style(
        "mypy",
        '''
        # https://mypy.readthedocs.io/en/latest/config_file.html
        ["setup.cfg".mypy]
        ignore_missing_imports = true

        # Do not follow imports (except for ones found in typeshed)
        follow_imports = "skip"

        # Treat Optional per PEP 484
        strict_optional = true

        # Ensure all execution paths are returning
        warn_no_return = true

        # Lint-style cleanliness for typing
        warn_redundant_casts = true
        warn_unused_ignores = true

        [[".pre-commit-config.yaml".repos]]
        yaml = """
          - repo: https://github.com/pre-commit/mirrors-mypy
            rev: v0.812
            hooks:
              - id: mypy
        """
    ''',
    ).named_style(
        "pre-commit/python",
        '''
        [[".pre-commit-config.yaml".repos]]
        yaml = """
          - repo: https://github.com/pre-commit/pygrep-hooks
            rev: v1.8.0
            hooks:
              - id: python-check-blanket-noqa
              - id: python-check-mock-methods
              - id: python-no-eval
              - id: python-no-log-warn
              - id: rst-backticks
          - repo: https://github.com/pre-commit/pre-commit-hooks
            rev: v4.0.1
            hooks:
              - id: debug-statements
          - repo: https://github.com/asottile/pyupgrade
            hooks:
              - id: pyupgrade
        """
        ''',
    ).named_style(
        "pre-commit/bash",
        '''
        [[".pre-commit-config.yaml".repos]]
        yaml = """
          - repo: https://github.com/openstack/bashate
            rev: 2.0.0
            hooks:
              - id: bashate
        """
        ''',
    ).pyproject_toml(
        """
        [tool.nitpick]
        style = ["root", "mypy", "pre-commit/python", "pre-commit/bash"]
        """
    ).pre_commit(
        datadir / "2-untouched-pre-commit.yaml"
    ).api_check_then_fix(
        partial_names=[PRE_COMMIT_CONFIG_YAML],
    ).assert_file_contents(
        PRE_COMMIT_CONFIG_YAML, datadir / "2-untouched-pre-commit.yaml"
    )


def test_pre_commit_section_without_dot_deprecated(tmp_path):
    """A pre-commit section without dot is deprecated."""
    project = (
        ProjectMock(tmp_path)
        .style(
            """
        ["pre-commit-config.yaml"]
        fail_fast = true
        """
        )
        .pre_commit("fail_fast: true")
    )

    with pytest.deprecated_call() as warning_list:
        project.flake8().assert_no_errors()

    filtered = filter_desired_warning(
        warning_list, 'The section name for dotfiles should start with a dot: [".pre-commit-config.yaml"]'
    )
    assert len(filtered) == 1
