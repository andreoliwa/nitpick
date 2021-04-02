"""Invoke targets.

Helpful docs:
- http://www.pyinvoke.org/
- http://docs.pyinvoke.org/en/stable/api/runners.html#invoke.runners.Runner.run
"""
from configparser import ConfigParser
from typing import Iterator

from invoke import Collection, task  # pylint: disable=import-error

COLOR_NONE = "\x1b[0m"
COLOR_GREEN = "\x1b[32m"
COLOR_BOLD_RED = "\x1b[1;31m"
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
def install(ctx, deps=True, hooks=False):
    """Install dependencies and pre-commit hooks.

    Poetry install is needed to create the Nitpick plugin entries on setuptools, used by pluggy.
    """
    if deps:
        print(f"{COLOR_GREEN}Nitpick runs in Python 3.6 and later, but development is done in 3.6{COLOR_NONE}")
        ctx.run("poetry env use python3.6")
        ctx.run("poetry install -E test -E lint -E doc --remove-untracked")
    if hooks:
        ctx.run("pre-commit install --install-hooks")
        ctx.run("pre-commit install --hook-type commit-msg")
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


@task(help={"coverage": "Run the HTML coverage report", "browse": "Browse the HTML coverage report"})
def test(ctx, coverage=False, browse=False):
    """Run tests and coverage using the commands from tox config."""
    tox = ToxCommands()
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
    tox_cmd = "tox -r" if recreate else "tox"
    if full:
        ctx.run(f"rm -rf {DOCS_BUILD_PATH} docs/source")
        ctx.run(tox_cmd)
    else:
        ctx.run(f"{tox_cmd} -e clean,lint,py38,docs,report")


@task(help={"recreate": "Recreate tox environment"})
def lint(ctx, recreate=False):
    """Lint using tox."""
    tox_cmd = "tox -r" if recreate else "tox"
    ctx.run(f"{tox_cmd} -e lint")


@task(help={"venv": "Remove the Poetry virtualenv"})
def clean(ctx, venv=False):
    """Clean build output and temp files."""
    ctx.run("find . -type f -name '*.py[co]' -print -delete")
    ctx.run("find . -type d -name '__pycache__' -print -delete")
    ctx.run(
        "find . -type d \\( -name '*.egg-info' -or -name 'pip-wheel-metadata' -or -name 'dist' \\) -print0 | "
        "xargs -0 rm -rvf"
    )
    ctx.run(f"rm -rvf .cache .mypy_cache {DOCS_BUILD_PATH} src/*.egg-info .pytest_cache .coverage htmlcov .tox")
    if venv:
        ctx.run("poetry env remove python3.6", warn=True)


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


namespace = Collection(install, update, test, pre_commit, doc, ci_build, lint, clean, reactions)
namespace.configure(
    {
        "run": {
            # Use a pseudo-terminal to display colorful output
            "pty": True,
        }
    }
)
