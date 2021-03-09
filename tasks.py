"""Invoke targets.

Helpful docs:
- http://www.pyinvoke.org/
- http://docs.pyinvoke.org/en/stable/api/runners.html#invoke.runners.Runner.run
"""
from configparser import ConfigParser
from typing import Iterator

from invoke import Collection, task

COLOR_GREEN = "\x1b[32m"
COLOR_NONE = "\x1b[0m"
DOCS_BUILD_PATH = "docs/_build"


class ToxCommands:
    """Tox commands read from the config file."""

    def __init__(self) -> None:
        self._parser = ConfigParser()
        self._parser.read("tox.ini")

    def list_commands(self, section: str) -> Iterator[str]:
        """List all commands in a section."""
        for line in self._parser[section]["commands"].splitlines():
            if not line:
                continue
            yield line

    def find_command(self, section: str, search: str) -> str:
        """Find a command on a section."""
        for line in self.list_commands(section):
            if search in line:
                return line.lstrip("- ")
        return ""

    @property
    def pytest_command(self):
        """Pytest."""
        return self.find_command("testenv", "pytest").replace("{posargs:", "").replace("}", "")

    def coverage_commands(self) -> Iterator[str]:
        """All coverage commands."""
        yield from self.list_commands("testenv:report")

    @property
    def generate_rst(self):
        """Generate RST."""
        return self.find_command("testenv:docs", "generate")

    @property
    def api(self):
        """Generate API docs."""
        return self.find_command("testenv:docs", "apidoc")

    @property
    def check_links(self):
        """Generate API docs."""
        return self.find_command("testenv:docs", "linkcheck").replace("{toxworkdir}", DOCS_BUILD_PATH)

    @property
    def html_docs(self):
        """Generate HTML docs."""
        return (
            self.find_command("testenv:docs", "html").replace("{posargs}", "").replace("{toxworkdir}", DOCS_BUILD_PATH)
        )


@task(help={"deps": "Poetry dependencies", "hooks": "pre-commit hooks"})
def install(c, deps=True, hooks=False):
    """Install dependencies and pre-commit hooks.

    Poetry install is needed to create the Nitpick plugin entries on setuptools, used by pluggy.
    """
    if deps:
        print(f"{COLOR_GREEN}Nitpick runs in Python 3.6 and later, but development is done in 3.6{COLOR_NONE}")
        c.run("poetry env use python3.6")
        c.run("poetry install -E test -E lint -E doc --remove-untracked")
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


@task(help={"coverage": "Run the HTML coverage report", "open": "Open the HTML coverage report"})
def test(c, coverage=False, open=False):
    """Run tests and coverage using the commands from tox config."""
    tox = ToxCommands()
    c.run(f"poetry run {tox.pytest_command}")

    if coverage:
        for cmd in tox.coverage_commands():
            c.run(f"poetry run {cmd}")

    if open:
        c.run("open htmlcov/index.html")


@task
def nitpick(c):
    """Run Nitpick locally on itself (with flake8)."""
    c.run("poetry run flake8 --select=NIP")


@task
def pylint(c):
    """Run pylint for all files."""
    c.run("poetry run pylint src/")


@task
def pre_commit(c):
    """Run pre-commit for all files."""
    c.run("pre-commit run --all-files")


@task(
    help={
        "full": "Run all steps",
        "recreate": "Delete and recreate RST for source files",
        "links": "Check links",
        "open": "Open the HTML index",
        "debug": "Debug HTML generation to fix warnings",
    }
)
def doc(c, full=False, recreate=False, links=False, open=False, debug=False):
    """Build documentation."""
    tox = ToxCommands()

    if full:
        recreate = links = True
    if recreate:
        c.run("mkdir -p docs/_static")
        c.run("rm -rf docs/source")

    c.run(f"poetry run {tox.generate_rst}")
    c.run(f"poetry run {tox.api}")
    if debug:
        c.run("poetry run sphinx-apidoc --help")
    if links:
        c.run(f"poetry run {tox.check_links}", warn=True)

    debug_options = "-nWT --keep-going -vvv" if debug else ""
    c.run(f"poetry run {tox.html_docs} {debug_options}")

    if open:
        c.run(f"open {DOCS_BUILD_PATH}/docs_out/index.html")


@task(help={"full": "Full build using tox", "recreate": "Recreate tox environment"})
def ci_build(c, full=False, recreate=False):
    """Simulate a CI build."""
    tox_cmd = "tox -r" if recreate else "tox"
    if full:
        c.run(f"rm -rf {DOCS_BUILD_PATH} docs/source")
        c.run(tox_cmd)
    else:
        c.run(f"{tox_cmd} -e clean,lint,py38,docs,report")


@task(help={"venv": "Remove the Poetry virtualenv"})
def clean(c, venv=False):
    """Clean build output and temp files."""
    c.run("find . -type f -name '*.py[co]' -print -delete")
    c.run("find . -type d -name '__pycache__' -print -delete")
    c.run(
        "find . -type d \\( -name '*.egg-info' -or -name 'pip-wheel-metadata' -or -name 'dist' \\) -print0 | "
        "xargs -0 rm -rvf"
    )
    c.run(f"rm -rvf .cache .mypy_cache {DOCS_BUILD_PATH} src/*.egg-info .pytest_cache .coverage htmlcov .tox")
    if venv:
        c.run("poetry env remove python3.6", warn=True)


namespace = Collection(install, update, test, nitpick, pylint, pre_commit, doc, ci_build, clean)
namespace.configure(
    {
        "run": {
            # Echo all commands in all tasks by default (like 'make' does)
            "echo": True,
            # Use a pseudo-terminal to display colorful output
            "pty": True,
        }
    }
)
