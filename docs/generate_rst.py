"""Generate .rst files content from Python classes. Run on the dev machine with "make doc", and commit on GitHub.

The ``include`` directive is not working on Read the Docs.
It doesn't recognise the "styles" dir anywhere (on the root, under "docs", under "_static"...).
Not even changing ``html_static_path`` on ``conf.py`` worked.
"""
import sys
from importlib import import_module
from pathlib import Path
from pprint import pprint
from subprocess import check_output  # nosec
from textwrap import dedent, indent
from typing import List

import click
from slugify import slugify
from sortedcontainers import SortedDict

from nitpick.constants import RAW_GITHUB_CONTENT_BASE_URL
from nitpick.core import Nitpick

DIVIDER = ".. auto-generated-from-here"
DOCS_DIR: Path = Path(__file__).parent.absolute()
STYLES_DIR: Path = DOCS_DIR.parent / "styles"

STYLE_MAPPING = SortedDict(
    {
        "black.toml": "black_",
        "flake8.toml": "flake8_",
        "isort.toml": "isort_",
        "mypy.toml": "mypy_",
        "absent-files.toml": "Absent files",
        "ipython.toml": "IPython_",
        "package-json.toml": "package.json_",
        "poetry.toml": "Poetry_",
        "pre-commit/bash.toml": "Bash_",
        "pre-commit/commitlint.toml": "commitlint_",
        "pre-commit/general.toml": "pre-commit_ (hooks)",
        "pre-commit/main.toml": "pre-commit_ (main)",
        "pre-commit/python.toml": "pre-commit_ (Python hooks)",
        "pylint.toml": "Pylint_",
        "pytest.toml": "pytest_",
        "python36.toml": "Python 3.6",
        "python37.toml": "Python 3.7",
        "python38.toml": "Python 3.8",
        "python39.toml": "Python 3.9",
    }
)
CLI_MAPPING = [
    ("", "Main options", ""),
    (
        "run",
        "Apply style to files",
        """
        At the end of execution, this command displays:

        - the number of fixed violations;
        - the number of violations that have to be changed manually.
        """,
    ),
    ("ls", "List configures files", ""),
]

nit = Nitpick.singleton().init()


def write_rst(filename: str, blocks: List[str]):
    """Write content to the .rst file."""
    rst_file: Path = DOCS_DIR / filename

    old_content = rst_file.read_text()
    cut_position = old_content.index(DIVIDER)
    new_content = old_content[: cut_position + len(DIVIDER) + 1]
    new_content += "\n".join(blocks)
    rst_file.write_text(new_content.strip() + "\n")
    click.secho(f"{rst_file} generated", fg="green")


def generate_defaults(filename: str):
    """Generate defaults.rst with hardcoded TOML content."""
    template = """
        .. _default-{link}:

        {header}
        {dashes}

        Contents of `{toml_file} <{base_url}/develop/{toml_file}>`_:

        .. code-block:: toml

        {toml_content}
    """
    clean_template = dedent(template).strip()
    blocks = []
    for toml_file, header in STYLE_MAPPING.items():
        style_path = STYLES_DIR / toml_file
        toml_content = style_path.read_text().strip()
        if not toml_content:
            # Skip empty TOML styles
            continue

        base_name = str(style_path.relative_to(STYLES_DIR.parent))
        indented_lines = [("    " + line.rstrip()).rstrip() for line in toml_content.split("\n")]
        blocks.append("")
        blocks.append(
            clean_template.format(
                link=slugify(header),
                header=header,
                dashes="-" * len(header),
                toml_file=base_name,
                base_url=RAW_GITHUB_CONTENT_BASE_URL,
                toml_content="\n".join(indented_lines),
            )
        )

    write_rst(filename, blocks)

    missing = SortedDict()
    for existing_toml_path in sorted(STYLES_DIR.glob("**/*.toml")):
        partial_name = str(existing_toml_path.relative_to(STYLES_DIR))
        if partial_name not in STYLE_MAPPING:
            missing[partial_name] = existing_toml_path.stem

    if missing:
        click.secho(
            f"ERROR: Add missing style files to the 'style_mapping' var in '{__file__}', as file/header pairs. Example:",
            fg="red",
        )
        pprint(missing)
        sys.exit(1)


def generate_plugins(filename: str) -> None:
    """Generate plugins.rst with the docstrings from :py:class:`nitpick.plugins.base.NitpickPlugin` classes."""
    template = """
        .. _{link}:

        {header}
        {dashes}

        {description}
    """
    clean_template = dedent(template).strip()
    blocks = []

    # Sort order: classes with fixed file names first, then alphabetically by class name
    for plugin_class in sorted(
        nit.project.plugin_manager.hook.plugin_class(),  # pylint: disable=no-member
        key=lambda c: "0" if c.filename else "1" + c.__name__,
    ):
        header = plugin_class.filename
        if not header:
            # module_name = file_class.__module__
            module = import_module(plugin_class.__module__)
            header = (module.__doc__ or "").strip(" .")

        blocks.append("")
        blocks.append(
            clean_template.format(
                link=slugify(plugin_class.__name__),
                header=header,
                dashes="-" * len(header),
                description=dedent(f"    {plugin_class.__doc__}").strip(),
            )
        )
    write_rst(filename, blocks)


def generate_cli(filename: str) -> None:
    """Generate CLI docs."""
    template = """
        {header}
        {dashes}
        {long}

        .. code-block::

        {help}
    """
    clean_template = dedent(template).strip()
    blocks = []

    for command, short, long in CLI_MAPPING:
        header = f"``{command}``: {short}" if command else short
        blocks.append("")
        parts = ["nitpick"]
        if command:
            parts.append(command)
        parts.append("--help")
        print(" ".join(parts))
        output = check_output(parts).decode().strip()  # nosec
        blocks.append(
            clean_template.format(
                header=header, dashes="-" * len(header), long=dedent(long), help=indent(output, "    ")
            )
        )

    write_rst(filename, blocks)


if __name__ == "__main__":
    generate_defaults("defaults.rst")
    generate_plugins("plugins.rst")
    generate_cli("cli.rst")
