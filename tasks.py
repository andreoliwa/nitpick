"""Invoke targets.

Helpful docs:
- https://www.pyinvoke.org/
- https://docs.pyinvoke.org/en/stable/api/runners.html#invoke.runners.Runner.run
"""
import sys
from configparser import ConfigParser
from typing import Iterator, List

from invoke import Collection, Exit, task  # pylint: disable=import-error

COLOR_NONE = "\x1b[0m"
COLOR_GREEN = "\x1b[32m"
COLOR_BOLD_RED = "\x1b[1;31m"
DOCS_BUILD_PATH = "docs/_build"

# pylint: disable=too-many-arguments


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
    def autofix_docs(self):
        """Autofix ReST documentation from docstrings and TOML."""
        return self.find_command("testenv:docs", "autofix_docs")

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
    def config(c) -> str:
        """Enable/disable macOS on tox.ini."""
        if sys.platform != "darwin":
            return ""

        temp_tox_ini = ".temp-tox.ini"
        # Hack to be able to run `invoke lint` on a macOS machine during development.
        c.run(f"sed 's/platform = linux/platform = darwin/g' tox.ini > {temp_tox_ini}")
        return f"-c {temp_tox_ini}"

    def _python_versions_old_to_new(self) -> List[str]:
        """Python versions executed in tox."""
        versions = []
        for py_plus_version_without_dot in self._parser["tox"]["envlist"].split(","):
            if not py_plus_version_without_dot.startswith("py"):
                continue

            major = py_plus_version_without_dot[2]
            minor = py_plus_version_without_dot[3:]
            versions.append(f"{major}.{minor}")
        return list(reversed(versions))

    @property
    def minimum_python_version(self) -> str:
        """Minimum Python version."""
        return self._python_versions_old_to_new()[0]

    @property
    def stable_python_version(self) -> str:
        """Stable Python version."""
        return self._as_tox_env(self._python_versions_old_to_new()[-2])

    @staticmethod
    def _as_tox_env(python_version_with_dot: str) -> str:
        no_dot = python_version_with_dot.replace(".", "")
        return f"py{no_dot}"


@task(help={"deps": "Poetry dependencies", "hooks": "pre-commit hooks"})
def install(c, deps=True, hooks=False):
    """Install dependencies and pre-commit hooks.

    Poetry install is needed to create the Nitpick plugin entries on setuptools, used by pluggy.
    """
    if deps:
        version = ToxCommands().minimum_python_version
        print(
            f"{COLOR_GREEN}Nitpick runs in Python {version} and later"
            f", but development is done in {version}{COLOR_NONE}"
        )
        c.run(f"poetry env use python{version}")
        c.run("poetry install -E test -E lint -E doc --remove-untracked")
    if hooks:
        c.run("pre-commit install -t pre-commit -t commit-msg --install-hooks")
        c.run("pre-commit gc")


@task(
    help={
        "file": "Choose (with fzf) a specific file to run tests",
        "coverage": "Run the HTML coverage report",
        "browse": "Browse the HTML coverage report",
        "watch": "Watch modified files and run tests with testmon",
        "reset": "Force testmon to update its data before watching tests",
    }
)
def test(c, file="", coverage=False, browse=False, watch=False, reset=False):
    """Run tests and coverage using the commands from tox config.

    `Testmon <https://github.com/tarpas/pytest-testmon>`_
    """
    tox = ToxCommands()
    if reset:
        c.run(f"poetry run {tox.pytest_command} --testmon-noselect")
        watch = True
    if watch:
        c.run('poetry run ptw --runner "pytest --testmon"')
        return

    file_opt = ""
    if file:
        from conjuring.grimoire import run_with_fzf  # pylint: disable=import-error,import-outside-toplevel

        chosen_file = run_with_fzf(c, "fd -H -t f test_.*.py", query=file)
        if not chosen_file:
            return
        file_opt = f" -- {chosen_file}"
    c.run(f"poetry run {tox.pytest_command}{file_opt}")

    if coverage:
        for cmd in tox.coverage_commands():
            c.run(f"poetry run {cmd}")

    if browse:
        c.run("open htmlcov/index.html")


@task(
    help={
        "full": "Run all steps",
        "recreate": "Delete and recreate RST for source files",
        "links": "Check links",
        "browse": "Browse the HTML index",
        "debug": "Debug HTML generation to fix warnings",
    }
)
def doc(c, full=False, recreate=False, links=False, browse=False, debug=False):
    """Build documentation."""
    tox = ToxCommands()

    if full:
        recreate = links = True
    if recreate:
        c.run("mkdir -p docs/_static")
        c.run(f"rm -rf {DOCS_BUILD_PATH} docs/source")

    c.run(f"poetry run {tox.autofix_docs}", warn=True)
    c.run(f"poetry run {tox.api}")
    if debug:
        c.run("poetry run sphinx-apidoc --help")

    debug_options = "-nWT --keep-going -vvv" if debug else ""
    c.run(f"poetry run {tox.html_docs} {debug_options}")

    if links:
        c.run(f"poetry run {tox.check_links}", warn=True)

    if browse:
        c.run(f"open {DOCS_BUILD_PATH}/docs_out/index.html")


@task(help={"full": "Full build using tox", "recreate": "Recreate tox environment", "docs": "Generate Sphinx docs"})
def ci_build(c, full=False, recreate=False, docs=True):
    """Simulate a CI build."""
    tox = ToxCommands()

    tox_cmd = " ".join(["tox", tox.config(c), "-r" if recreate else ""])
    if full:
        c.run(f"rm -rf {DOCS_BUILD_PATH} docs/source")
        c.run(tox_cmd)
    else:
        envs = ["clean", "lint", ToxCommands().stable_python_version]
        if docs:
            envs.append("docs")
        envs.append("report")
        c.run(f"{tox_cmd} -e {','.join(envs)}")


@task(help={"recreate": "Recreate tox environment"})
def lint(c, recreate=False):
    """Lint using tox."""
    tox = ToxCommands()

    tox_cmd = "tox -r" if recreate else "tox"
    result = c.run(f"{tox_cmd}{tox.config(c)} -e lint", warn=True)

    # Exit only after restoring tox.ini
    if result.exited > 0:
        raise Exit("pylint failed", 1)


@task(help={"venv": "Remove the Poetry virtualenv and the tox dir"})
def clean(c, venv=False):
    """Clean build output and temp files."""
    c.run("find . -type f -name '*.py[co]' -print -delete")
    c.run("find . -type d -name '__pycache__' -print -delete")
    c.run("find . -type d \\( -name '*.egg-info' -or -name 'pip-wheel-metadata' -or -name 'dist' \\) -print -delete")
    c.run(f"rm -rf .cache .mypy_cache {DOCS_BUILD_PATH} src/*.egg-info .pytest_cache .coverage htmlcov .testmondata")
    if venv:
        c.run("rm -rf .tox")
        version = ToxCommands().minimum_python_version
        c.run(f"poetry env remove python{version}", warn=True)


@task
def reactions(c):
    """List issues with reactions.

    https://github.blog/2021-03-11-scripting-with-github-cli/
    https://docs.github.com/en/rest/reference/issues#get-an-issue
    https://developer.github.com/changes/2016-05-12-reactions-api-preview/
    """
    result = c.run("gh api -X GET 'repos/andreoliwa/nitpick/issues' --paginate --jq '.[].number'", pty=False)
    for issue in result.stdout.splitlines():
        result_users = c.run(
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


@task(
    help={
        "convert_file_name": "Partial name of the file you want to convert into a Nitpick TOML style",
        "lab_help": "Display the help for the lab CLI (a Click CLI within an Invoke CLI... CLI inception!)",
    }
)
def lab(c, convert_file_name="", lab_help=False):
    """Laboratory of experiments and ideas. You need to install certain tools if you want to use this command.

    Pre-requisites:
    - https://github.com/andreoliwa/conjuring
    - https://github.com/junegunn/fzf
    - https://github.com/sharkdp/fd
    """
    extra_args = []
    if lab_help:
        extra_args.append("--help")
    if convert_file_name:
        from conjuring.grimoire import run_with_fzf  # pylint: disable=import-error,import-outside-toplevel

        chosen_file = run_with_fzf(c, "fd -H -t f", query=convert_file_name)
        extra_args.extend(["convert", chosen_file])

    c.run(f"poetry run python docs/ideas/lab.py {' '.join(extra_args)}")


namespace = Collection(install, test, doc, ci_build, lint, clean, reactions, lab)
namespace.configure(
    {
        "run": {
            # Use a pseudo-terminal to display colorful output
            "pty": True
        }
    }
)
