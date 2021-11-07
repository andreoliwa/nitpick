"""Invoke targets.

Helpful docs:
- https://www.pyinvoke.org/
- https://docs.pyinvoke.org/en/stable/api/runners.html#invoke.runners.Runner.run
"""
import sys
from configparser import ConfigParser
from typing import Iterator

from invoke import Collection, Exit, task  # pylint: disable=import-error

COLOR_NONE = "\x1b[0m"
COLOR_GREEN = "\x1b[32m"
COLOR_BOLD_RED = "\x1b[1;31m"
DOCS_BUILD_PATH = "docs/_build"

# TODO: read from tox.ini instead
MINIMUM_PYTHON_VERSION = "3.6"
STABLE_PYTHON_VERSION = "py39"


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

    @staticmethod
    def macos(ctx, enable: bool):
        """Enable/disable macOS on tox.ini."""
        if sys.platform != "darwin":
            return

        if enable:
            # Hack to be able to run `invoke lint` on a macOS machine during development.
            ctx.run("sed -i '' 's/platform = linux/platform = darwin/g' tox.ini")
        else:
            ctx.run("sed -i '' 's/platform = darwin/platform = linux/g' tox.ini")


@task(help={"deps": "Poetry dependencies", "hooks": "pre-commit hooks"})
def install(ctx, deps=True, hooks=False):
    """Install dependencies and pre-commit hooks.

    Poetry install is needed to create the Nitpick plugin entries on setuptools, used by pluggy.
    """
    if deps:
        print(
            f"{COLOR_GREEN}Nitpick runs in Python {MINIMUM_PYTHON_VERSION} and later"
            f", but development is done in {MINIMUM_PYTHON_VERSION}{COLOR_NONE}"
        )
        ctx.run(f"poetry env use python{MINIMUM_PYTHON_VERSION}")
        ctx.run("poetry install -E test -E lint -E doc --remove-untracked")
    if hooks:
        ctx.run("pre-commit install -t pre-commit -t commit-msg --install-hooks")
        ctx.run("pre-commit gc")


@task(help={"deps": "Update Poetry dependencies", "hooks": "Update pre-commit hooks"})
def update(ctx, deps=True, hooks=False):
    """Update pre-commit hooks and Poetry dependencies."""
    if hooks:
        # Uncomment the line below to auto update all repos except a few filtered out with egrep
        ctx.run(
            "yq -r '.repos[].repo' .pre-commit-config.yaml | egrep -v -e '^local' -e commitlint"
            " | sed -E -e 's/http/--repo http/g' | xargs pre-commit autoupdate"
        )

    if deps:
        ctx.run("poetry update")

    # Also install what was updated
    install(ctx, deps, hooks)


@task(
    help={
        "coverage": "Run the HTML coverage report",
        "browse": "Browse the HTML coverage report",
        "watch": "Watch modified files and run tests with testmon",
    }
)
def test(ctx, coverage=False, browse=False, watch=False):
    """Run tests and coverage using the commands from tox config."""
    tox = ToxCommands()
    if watch:
        ctx.run('poetry run ptw --runner "pytest --testmon"')
        return

    ctx.run(f"poetry run {tox.pytest_command}")

    if coverage:
        for cmd in tox.coverage_commands():
            ctx.run(f"poetry run {cmd}")

    if browse:
        ctx.run("open htmlcov/index.html")


@task(help={"hook": "Specific hook to run"})
def pre_commit(ctx, hook=""):
    """Run pre-commit for all files."""
    ctx.run(f"pre-commit run --all-files {hook}")


@task(
    help={
        "full": "Run all steps",
        "recreate": "Delete and recreate RST for source files",
        "links": "Check links",
        "browse": "Browse the HTML index",
        "debug": "Debug HTML generation to fix warnings",
    }  # pylint: disable=too-many-arguments
)
def doc(ctx, full=False, recreate=False, links=False, browse=False, debug=False):
    """Build documentation."""
    tox = ToxCommands()

    if full:
        recreate = links = True
    if recreate:
        ctx.run("mkdir -p docs/_static")
        ctx.run(f"rm -rf {DOCS_BUILD_PATH} docs/source")

    ctx.run(f"poetry run {tox.generate_rst}")
    ctx.run(f"poetry run {tox.api}")
    if debug:
        ctx.run("poetry run sphinx-apidoc --help")

    debug_options = "-nWT --keep-going -vvv" if debug else ""
    ctx.run(f"poetry run {tox.html_docs} {debug_options}")

    if links:
        ctx.run(f"poetry run {tox.check_links}", warn=True)

    if browse:
        ctx.run(f"open {DOCS_BUILD_PATH}/docs_out/index.html")


@task(help={"full": "Full build using tox", "recreate": "Recreate tox environment"})
def ci_build(ctx, full=False, recreate=False):
    """Simulate a CI build."""
    tox = ToxCommands()
    tox.macos(ctx, True)

    tox_cmd = "tox -r" if recreate else "tox"
    if full:
        ctx.run(f"rm -rf {DOCS_BUILD_PATH} docs/source")
        ctx.run(tox_cmd)
    else:
        ctx.run(f"{tox_cmd} -e clean,lint,{STABLE_PYTHON_VERSION},docs,report")

    tox.macos(ctx, False)


@task(help={"recreate": "Recreate tox environment"})
def lint(ctx, recreate=False):
    """Lint using tox."""
    tox = ToxCommands()
    tox.macos(ctx, True)

    tox_cmd = "tox -r" if recreate else "tox"
    result = ctx.run(f"{tox_cmd} -e lint", warn=True)

    tox.macos(ctx, False)

    # Exit only after restoring tox.ini
    if result.exited > 0:
        raise Exit("pylint failed", 1)


@task(help={"venv": "Remove the Poetry virtualenv and the tox dir"})
def clean(ctx, venv=False):
    """Clean build output and temp files."""
    ctx.run("find . -type f -name '*.py[co]' -print -delete")
    ctx.run("find . -type d -name '__pycache__' -print -delete")
    ctx.run("find . -type d \\( -name '*.egg-info' -or -name 'pip-wheel-metadata' -or -name 'dist' \\) -print -delete")
    ctx.run(f"rm -rf .cache .mypy_cache {DOCS_BUILD_PATH} src/*.egg-info .pytest_cache .coverage htmlcov .testmondata")
    if venv:
        ctx.run("rm -rf .tox")
        ctx.run(f"poetry env remove python{MINIMUM_PYTHON_VERSION}", warn=True)


@task
def reactions(ctx):
    """List issues with reactions.

    https://github.blog/2021-03-11-scripting-with-github-cli/
    https://docs.github.com/en/rest/reference/issues#get-an-issue
    https://developer.github.com/changes/2016-05-12-reactions-api-preview/
    """
    result = ctx.run("gh api -X GET 'repos/andreoliwa/nitpick/issues' | jq -r '.[].number'", pty=False)
    for issue in result.stdout.splitlines():
        result_users = ctx.run(
            f"gh api -X GET 'repos/andreoliwa/nitpick/issues/{int(issue)}/reactions'"
            " -H 'Accept: application/vnd.github.squirrel-girl-preview'"
            " | jq -r '.[].user.html_url'"
        )
        users = result_users.stdout.splitlines()
        if users:
            print(COLOR_GREEN)
            print(f">>> https://github.com/andreoliwa/nitpick/issues/{issue}")
            for index, user in enumerate(users):
                print(f"    {index + 1}. {user}")
            print(COLOR_NONE)


@task
def lab(ctx):
    """Laboratory of ideas."""
    ctx.run("poetry run python docs/ideas/lab.py")


namespace = Collection(install, update, test, pre_commit, doc, ci_build, lint, clean, reactions, lab)
namespace.configure(
    {
        "run": {
            # Use a pseudo-terminal to display colorful output
            "pty": True
        }
    }
)
