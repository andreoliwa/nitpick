"""Invoke targets.

Helpful docs:
- http://www.pyinvoke.org/
- http://docs.pyinvoke.org/en/stable/api/runners.html#invoke.runners.Runner.run
"""
from invoke import Collection, task


@task(help={"deps": "Poetry dependencies", "hooks": "pre-commit hooks"})
def install(c, deps=True, hooks=False):
    """Install dependencies and pre-commit hooks.

    Poetry install is needed to create the Nitpick plugin entries on setuptools, used by pluggy.
    """
    if deps:
        c.run("poetry env use python3.6")
        c.run("poetry install -E test -E lint", pty=True)
    if hooks:
        c.run("pre-commit install --install-hooks")
        c.run("pre-commit install --hook-type commit-msg")
        c.run("pre-commit gc")


@task(help={"poetry": "Update Poetry dependencies", "pre_commit": "Update pre-commit hooks"})
def update(c, poetry=True, pre_commit=False):
    """Update pre-commit hooks and Poetry dependencies."""
    if pre_commit:
        # Uncomment the line below to auto update all repos except a few filtered out with egrep
        c.run(
            "yq -r '.repos[].repo' .pre-commit-config.yaml | egrep -v -e '^local' -e commitlint"
            " | sed -E -e 's/http/--repo http/g' | xargs pre-commit autoupdate"
        )

    if poetry:
        c.run("poetry update")


@task
def test(c):
    """Run tests with pytest."""
    # https://docs.pytest.org/en/stable/skipping.html
    c.run("poetry run python -m pytest --doctest-modules -s -rxXs", pty=True)


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


@task
def ci_build(c, full=False, recreate=False):
    """Simulate a CI build."""
    tox_cmd = "tox -r" if recreate else "tox"
    if full:
        c.run("rm -rf docs/_build docs/source")
        c.run(tox_cmd)
    else:
        c.run(f"{tox_cmd} -e clean,lint,py38,docs,report")


namespace = Collection(install, update, test, nitpick, pylint, pre_commit, doc, ci_build)
# Echo all commands in all tasks by default (like 'make' does)
namespace.configure({"run": {"echo": True}})
