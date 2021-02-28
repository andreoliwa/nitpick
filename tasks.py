"""Invoke targets.

Helpful docs:
- http://www.pyinvoke.org/
- http://docs.pyinvoke.org/en/stable/api/runners.html#invoke.runners.Runner.run
"""
from configparser import ConfigParser

from invoke import Collection, task


@task(help={"deps": "Poetry dependencies", "hooks": "pre-commit hooks"})
def install(c, deps=True, hooks=False):
    """Install dependencies and pre-commit hooks.

    Poetry install is needed to create the Nitpick plugin entries on setuptools, used by pluggy.
    """
    if deps:
        c.run("poetry env use python3.6")
        c.run("poetry install -E test -E lint --remove-untracked", pty=True)
    if hooks:
        c.run("pre-commit install --install-hooks")
        c.run("pre-commit install --hook-type commit-msg")
        c.run("pre-commit gc")


@task(help={"deps": "Update Poetry dependencies", "hooks": "Update pre-commit hooks"})
def update(c, deps=True, hooks=False):
    """Update pre-commit hooks and Poetry dependencies."""
    if hooks:
        # Uncomment the line below to auto update all repos except a few filtered out with egrep
        c.run(
            "yq -r '.repos[].repo' .pre-commit-config.yaml | egrep -v -e '^local' -e commitlint"
            " | sed -E -e 's/http/--repo http/g' | xargs pre-commit autoupdate"
        )

    if deps:
        c.run("poetry update")

    # Also install what was updated
    install(c, deps, hooks)


@task
def test(c):
    """Run tests with pytest; use the command from tox config."""
    parser = ConfigParser()
    parser.read("setup.cfg")
    pytest_cmd = (
        [line for line in parser["testenv"]["commands"].splitlines() if "pytest" in line][0]
        .replace("{posargs:", "")
        .replace("}", "")
    )
    c.run(f"poetry run {pytest_cmd}", pty=True)


@task
def nitpick(c):
    """Run Nitpick locally on itself (with flake8)."""
    c.run("poetry run flake8 --select=NIP")


@task
def pylint(c):
    """Run pylint for all files."""
    c.run("poetry run pylint src/", pty=True)


@task
def pre_commit(c):
    """Run pre-commit for all files."""
    c.run("pre-commit run --all-files", pty=True)


@task
def doc(c):
    """Build documentation."""
    c.run("mkdir -p docs/_static")
    c.run("rm -rf docs/source")
    c.run("tox -e docs")


@task(help={"full": "Full build using tox", "recreate": "Recreate tox environment"})
def ci_build(c, full=False, recreate=False):
    """Simulate a CI build."""
    tox_cmd = "tox -r" if recreate else "tox"
    if full:
        c.run("rm -rf docs/_build docs/source")
        c.run(tox_cmd)
    else:
        c.run(f"{tox_cmd} -e clean,lint,py38,docs,report")


@task
def clean(c):
    """Clean build output and temp files."""
    c.run("find . -type f -name '*.py[co]' -print -delete")
    c.run("find . -type d -name '__pycache__' -print -delete")
    c.run(
        "find . -type d \\( -name '*.egg-info' -or -name 'pip-wheel-metadata' -or -name 'dist' \\) -print0 | "
        "xargs -0 rm -rvf"
    )
    c.run("rm -rvf .cache .mypy_cache docs/_build src/*.egg-info .pytest_cache .coverage htmlcov .tox")


namespace = Collection(install, update, test, nitpick, pylint, pre_commit, doc, ci_build, clean)
# Echo all commands in all tasks by default (like 'make' does)
namespace.configure({"run": {"echo": True}})
