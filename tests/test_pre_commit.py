"""Pre-commit tests."""
from textwrap import dedent

from testfixtures import compare

from nitpick.plugins.pre_commit import PreCommitHook
from tests.helpers import ProjectMock


def test_pre_commit_has_no_configuration(request):
    """No errors should be raised if pre-commit is not referenced in any style file.

    Also the file should not be deleted unless explicitly asked.
    """
    ProjectMock(request).style("").pre_commit("").flake8().assert_no_errors()


def test_pre_commit_referenced_in_style(request):
    """Only check files if they have configured styles."""
    ProjectMock(request).style(
        """
        ["pre-commit-config.yaml"]
        fail_fast = true
        """
    ).pre_commit("").flake8().assert_single_error(
        "NIP331 File .pre-commit-config.yaml doesn't have the 'repos' root key"
    )


def test_suggest_initial_contents(request):
    """Suggest initial contents for missing pre-commit config file."""
    ProjectMock(request).load_styles("isort", "black").pyproject_toml(
        """
        [tool.nitpick]
        style = ["isort", "black"]
        """
    ).flake8().assert_errors_contain(
        """
        NIP331 File .pre-commit-config.yaml was not found. Create it with this content:\x1b[32m
        repos:
          - repo: https://github.com/asottile/seed-isort-config
            rev: v2.2.0
            hooks:
              - id: seed-isort-config
          - repo: https://github.com/pre-commit/mirrors-isort
            rev: v5.5.2
            hooks:
              - id: isort
          - repo: https://github.com/python/black
            rev: 20.8b1
            hooks:
              - id: black
                args: [--safe, --quiet]
          - repo: https://github.com/asottile/blacken-docs
            rev: v1.8.0
            hooks:
              - id: blacken-docs
                additional_dependencies: [black==20.8b1]\x1b[0m
        """
    )


def test_root_values_on_missing_file(request):
    """Test values on the root of the config file when it's missing."""
    ProjectMock(request).style(
        """
        ["pre-commit-config.yaml"]
        bla_bla = "oh yeah"
        fail_fast = true
        whatever = "1"
        """
    ).flake8().assert_errors_contain_unordered(
        """
        NIP331 File .pre-commit-config.yaml was not found. Create it with this content:\x1b[32m
        bla_bla: oh yeah
        fail_fast: true
        whatever: '1'\x1b[0m
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
    ).flake8().assert_errors_contain_unordered(
        """
        NIP338 File .pre-commit-config.yaml has missing values:\x1b[32m
        blabla: what
        fail_fast: true\x1b[0m
        """
    ).assert_errors_contain(
        """
        NIP339 File .pre-commit-config.yaml has different values. Use this:\x1b[32m
        another_thing: yep
        something: true\x1b[0m
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
    ).flake8().assert_errors_contain(
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
    ).flake8().assert_single_error(
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
    ).flake8().assert_single_error(
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
    ).flake8().assert_single_error(
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
    ).flake8().assert_single_error(
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
    ).flake8().assert_single_error(
        """
        NIP336 File .pre-commit-config.yaml: style file is missing 'id' in hook:
            name: isort
            entry: isort -sp setup.cfg
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
    ).flake8().assert_single_error(
        """
        NIP337 File .pre-commit-config.yaml: missing hook with id 'black':
          - id: black
            name: black
            entry: black
        """
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


def test_missing_different_values(request):
    """Test missing and different values on the hooks."""
    # TODO: add loaded and named styles automatically to pyproject_toml
    # pylint: disable=line-too-long
    ProjectMock(request).named_style(
        "root",
        '''
        [["pre-commit-config.yaml".repos]]
        yaml = """
          - repo: https://github.com/user/repo
            rev: 1.2.3
            hooks:
              - id: my-hook
                args: [--expected, arguments]
        """
        ''',
    ).load_styles("mypy", "pre-commit/python", "pre-commit/bash").pyproject_toml(
        """
        [tool.nitpick]
        style = ["root", "mypy", "pre-commit/python", "pre-commit/bash"]
        """
    ).setup_cfg(
        """
        [mypy]
        follow_imports = skip
        ignore_missing_imports = True
        strict_optional = True
        warn_no_return = True
        warn_redundant_casts = True
        warn_unused_ignores = True
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
    ).flake8().assert_errors_contain(
        """
        NIP332 File .pre-commit-config.yaml: hook 'mypy' not found. Use this:\x1b[32m
          - repo: https://github.com/pre-commit/mirrors-mypy
            rev: v0.782
            hooks:
              - id: mypy\x1b[0m
        """
    ).assert_errors_contain(
        """
        NIP332 File .pre-commit-config.yaml: hook 'python-check-mock-methods' not found. Use this:\x1b[32m
          - repo: https://github.com/pre-commit/pygrep-hooks
            rev: v1.6.0
            hooks:
              - id: python-check-mock-methods\x1b[0m
        """
    ).assert_errors_contain(
        """
        NIP339 File .pre-commit-config.yaml: hook 'bashate' (rev: 0.5.0) has different values. Use this:\x1b[32m
        rev: 2.0.0\x1b[0m
        """
    ).assert_errors_contain(
        """
        NIP339 File .pre-commit-config.yaml: hook 'python-check-blanket-noqa' (rev: v1.1.0) has different values. Use this:\x1b[32m
        rev: v1.6.0\x1b[0m
        """
    ).assert_errors_contain(
        """
        NIP339 File .pre-commit-config.yaml: hook 'python-no-eval' (rev: v1.1.0) has different values. Use this:\x1b[32m
        rev: v1.6.0\x1b[0m
        """
    ).assert_errors_contain(
        """
        NIP339 File .pre-commit-config.yaml: hook 'python-no-log-warn' (rev: v1.1.0) has different values. Use this:\x1b[32m
        rev: v1.6.0\x1b[0m
        """
    ).assert_errors_contain(
        """
        NIP339 File .pre-commit-config.yaml: hook 'my-hook' (rev: 1.2.3) has different values. Use this:\x1b[32m
        args:
          - --expected
          - arguments\x1b[0m
        """
    ).assert_errors_contain(
        """
        NIP339 File .pre-commit-config.yaml: hook 'rst-backticks' (rev: v1.1.0) has different values. Use this:\x1b[32m
        rev: v1.6.0\x1b[0m
        """,
        8,
    )
