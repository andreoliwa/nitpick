"""Pre-commit tests."""
from textwrap import dedent

import pytest
from testfixtures import compare

from nitpick.constants import PRE_COMMIT_CONFIG_YAML, SETUP_CFG
from nitpick.plugins.pre_commit import PreCommitHook
from nitpick.violations import Fuss
from tests.helpers import NBSP, ProjectMock


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
    ).pre_commit("").api_check_then_fix(Fuss(False, PRE_COMMIT_CONFIG_YAML, 331, " doesn't have the 'repos' root key"))


def test_suggest_initial_contents(tmp_path):
    """Suggest initial contents for missing pre-commit config file."""
    ProjectMock(tmp_path).named_style(
        "isort",
        '''
        ["setup.cfg".isort]
        line_length = 120
        skip = ".tox,build"
        known_first_party = "tests"

        # The configuration below is needed for compatibility with black.
        # https://github.com/python/black#how-black-wraps-lines
        # https://github.com/PyCQA/isort#multi-line-output-modes
        multi_line_output = 3
        include_trailing_comma = true
        force_grid_wrap = 0
        combine_as_imports = true

        [[".pre-commit-config.yaml".repos]]
        yaml = """
          - repo: https://github.com/PyCQA/isort
            rev: 5.8.0
            hooks:
              - id: isort
        """
        ''',
    ).named_style(
        "black",
        '''
        ["pyproject.toml".tool.black]
        line-length = 120

        [[".pre-commit-config.yaml".repos]]
        yaml = """
          - repo: https://github.com/psf/black
            rev: 21.5b2
            hooks:
              - id: black
                args: [--safe, --quiet]
          - repo: https://github.com/asottile/blacken-docs
            rev: v1.10.0
            hooks:
              - id: blacken-docs
                additional_dependencies: [black==21.5b2]
        """
        # TODO The toml library has issues loading arrays with multiline strings:
        #  https://github.com/uiri/toml/issues/123
        #  https://github.com/uiri/toml/issues/230
        #  If they are fixed one day, remove this 'yaml' key and use only a 'repos' list with a single element:
        #[".pre-commit-config.yaml"]
        #repos = ["""
        #<YAML goes here>
        #"""]
        ''',
    ).pyproject_toml(
        """
        [tool.nitpick]
        style = ["isort", "black"]
        """
    ).api_check_then_fix(
        Fuss(
            False,
            PRE_COMMIT_CONFIG_YAML,
            331,
            " was not found. Create it with this content:",
            """
            repos:
              - repo: https://github.com/PyCQA/isort
                rev: 5.8.0
                hooks:
                  - id: isort
              - repo: https://github.com/psf/black
                rev: 21.5b2
                hooks:
                  - id: black
                    args: [--safe, --quiet]
              - repo: https://github.com/asottile/blacken-docs
                rev: v1.10.0
                hooks:
                  - id: blacken-docs
                    additional_dependencies: [black==21.5b2]
            """,
        ),
        partial_names=[PRE_COMMIT_CONFIG_YAML],
    )


def test_no_yaml_key(tmp_path):
    """Test an invalid repo config."""
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
            False,
            PRE_COMMIT_CONFIG_YAML,
            331,
            " was not found. Create it with this content:",
            """
            repos: []
            """,
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
            False,
            PRE_COMMIT_CONFIG_YAML,
            331,
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
            False,
            PRE_COMMIT_CONFIG_YAML,
            338,
            " has missing values:",
            """
            blabla: what
            fail_fast: true
            """,
        ),
        Fuss(
            False,
            PRE_COMMIT_CONFIG_YAML,
            339,
            " has different values. Use this:",
            """
            another_thing: yep
            something: true
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
        Fuss(False, PRE_COMMIT_CONFIG_YAML, 331, " doesn't have the 'repos' root key")
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
        Fuss(False, PRE_COMMIT_CONFIG_YAML, 332, ": style file is missing 'repo' key in repo #0")
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
        Fuss(False, PRE_COMMIT_CONFIG_YAML, 333, ": repo 'local' does not exist under 'repos'")
    )


def test_missing_hooks_in_repo(tmp_path):
    """Test missing hooks in repo."""
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
    ).api_check_then_fix(
        Fuss(False, PRE_COMMIT_CONFIG_YAML, 334, ": missing 'hooks' in repo 'whatever'")
    )


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
        Fuss(False, PRE_COMMIT_CONFIG_YAML, 335, ": style file is missing 'hooks' in repo 'another'")
    )


def test_style_missing_id_in_hook(tmp_path):
    """Test style file is missing id in hook."""
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
            False,
            PRE_COMMIT_CONFIG_YAML,
            336,
            ": style file is missing 'id' in hook:",
            f"""
            {NBSP*4}name: isort
            {NBSP*4}entry: isort -sp {SETUP_CFG}
            """,
        )
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
            False,
            PRE_COMMIT_CONFIG_YAML,
            337,
            ": missing hook with id 'black':",
            f"""
            {NBSP * 2}- id: black
            {NBSP * 2}  name: black
            {NBSP * 2}  entry: black
            """,
        )
    )


def test_get_all_hooks_from():
    """Test if the get_all_hooks_from() method will split the YAML block in hooks and copy the repo info for each."""
    data = """
      - repo: https://github.com/user/repo
        rev: v0.4.5
        hooks:
          - id: first
            additional_dependencies: [package==1.0.0]
          - id: second
            args: [1, 2, 3]
          - id: third
          - id: fourth
            args: [some, here]
            additional_dependencies: [another>=2.0.3]
    """
    rv = PreCommitHook.get_all_hooks_from(dedent(data))

    def assert_hook_yaml(key, yaml_string):
        expected = rv["https://github.com/user/repo_" + key].yaml.reformatted
        actual = yaml_string
        compare(dedent(actual).strip(), dedent(expected).strip())

    assert_hook_yaml(
        "first",
        """
          - repo: https://github.com/user/repo
            rev: v0.4.5
            hooks:
              - id: first
                additional_dependencies: [package==1.0.0]
        """,
    )
    assert_hook_yaml(
        "second",
        """
          - repo: https://github.com/user/repo
            rev: v0.4.5
            hooks:
              - id: second
                args: [1, 2, 3]
        """,
    )
    assert_hook_yaml(
        "third",
        """
          - repo: https://github.com/user/repo
            rev: v0.4.5
            hooks:
              - id: third
        """,
    )
    assert_hook_yaml(
        "fourth",
        """
          - repo: https://github.com/user/repo
            rev: v0.4.5
            hooks:
              - id: fourth
                args: [some, here]
                additional_dependencies: [another>=2.0.3]
        """,
    )


def test_missing_different_values(tmp_path):
    """Test missing and different values on the hooks."""
    ProjectMock(tmp_path).named_style(
        "root",
        '''
        [[".pre-commit-config.yaml".repos]]
        yaml = """
          - repo: https://github.com/user/repo
            rev: 1.2.3
            hooks:
              - id: my-hook
                args: [--expected, arguments]
        """
        ''',
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
        """
        repos:
          - repo: https://github.com/pre-commit/pygrep-hooks
            rev: v1.1.0
            hooks:
              - id: python-check-blanket-noqa
              - id: missing-hook-in-this-position
              - id: python-no-eval
              - id: python-no-log-warn
              - id: rst-backticks
          - repo: https://github.com/pre-commit/pre-commit-hooks
            rev: v4.0.1
            hooks:
              - id: debug-statements
          - repo: https://github.com/asottile/pyupgrade
            rev: v2.16.0
            hooks:
              - id: pyupgrade
          - repo: https://github.com/openstack/bashate
            rev: 0.5.0
            hooks:
              - id: extra-hook-before-should-be-ignored
              - id: bashate
                args: [extra, arguments, should, --not, --throw, errors]
              - id: extra-hook-after-should-be-ignored
          - repo: https://github.com/user/repo
            rev: 1.2.3
            hooks:
              - id: my-hook
                args: [--different, args, --should, throw, errors]
        """
    ).api_check_then_fix(
        Fuss(
            False,
            PRE_COMMIT_CONFIG_YAML,
            332,
            ": hook 'mypy' not found. Use this:",
            f"""
            {NBSP * 2}- repo: https://github.com/pre-commit/mirrors-mypy
                rev: v0.812
                hooks:
                  - id: mypy
            """,
        ),
        Fuss(
            False,
            PRE_COMMIT_CONFIG_YAML,
            332,
            ": hook 'python-check-mock-methods' not found. Use this:",
            f"""
            {NBSP * 2}- repo: https://github.com/pre-commit/pygrep-hooks
                rev: v1.8.0
                hooks:
                  - id: python-check-mock-methods
            """,
        ),
        Fuss(
            False,
            PRE_COMMIT_CONFIG_YAML,
            339,
            ": hook 'bashate' (rev: 0.5.0) has different values. Use this:",
            "rev: 2.0.0",
        ),
        Fuss(
            False,
            PRE_COMMIT_CONFIG_YAML,
            339,
            ": hook 'python-check-blanket-noqa' (rev: v1.1.0) has different values. Use this:",
            "rev: v1.8.0",
        ),
        Fuss(
            False,
            PRE_COMMIT_CONFIG_YAML,
            339,
            ": hook 'python-no-eval' (rev: v1.1.0) has different values. Use this:",
            "rev: v1.8.0",
        ),
        Fuss(
            False,
            PRE_COMMIT_CONFIG_YAML,
            339,
            ": hook 'python-no-log-warn' (rev: v1.1.0) has different values. Use this:",
            "rev: v1.8.0",
        ),
        Fuss(
            False,
            PRE_COMMIT_CONFIG_YAML,
            339,
            ": hook 'my-hook' (rev: 1.2.3) has different values. Use this:",
            """
            args:
              - --expected
              - arguments
            """,
        ),
        Fuss(
            False,
            PRE_COMMIT_CONFIG_YAML,
            339,
            ": hook 'rst-backticks' (rev: v1.1.0) has different values. Use this:",
            "rev: v1.8.0",
        ),
        partial_names=[PRE_COMMIT_CONFIG_YAML],
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
        .pre_commit("")
    )

    with pytest.deprecated_call() as warning_list:
        project.flake8().assert_single_error("NIP331 File .pre-commit-config.yaml doesn't have the 'repos' root key")

    assert len(warning_list) == 1
    assert (
        str(warning_list[0].message)
        == 'The section name for dotfiles should start with a dot: [".pre-commit-config.yaml"]'
    )
