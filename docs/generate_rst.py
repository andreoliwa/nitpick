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

from nitpick import __version__
from nitpick.constants import GITHUB_BASE_URL, CONFIG_FILES
from nitpick.core import Nitpick

DIVIDER_FROM_HERE = ".. auto-generated-from-here"
DIVIDER_START = ".. auto-generated-start-{}"
DIVIDER_END = ".. auto-generated-end-{}"
DOCS_DIR: Path = Path(__file__).parent.absolute()
STYLES_DIR: Path = DOCS_DIR.parent / "styles"

STYLE_MAPPING = SortedDict(
    {
        "absent-files.toml": "Absent files",
        "black.toml": "black_",
        "editorconfig.toml": "EditorConfig_",
        "flake8.toml": "flake8_",
        "ipython.toml": "IPython_",
        "isort.toml": "isort_",
        "mypy.toml": "mypy_",
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
        "tox.toml": "tox_",
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
    ("init", "Initialise a configuration file", ""),
]

nit = Nitpick.singleton().init()


def write_rst(filename: str, blocks: List[str], divider_id: str = None) -> int:
    """Write content to the .rst file."""
    rst_file: Path = DOCS_DIR / filename

    old_content = rst_file.read_text()
    if divider_id:
        start_marker = DIVIDER_START.format(divider_id)
        end_marker = DIVIDER_END.format(divider_id)
        start_position = old_content.index(start_marker) + len(start_marker) + 1
        end_position = old_content.index(end_marker) - 1
    else:
        start_position = old_content.index(DIVIDER_FROM_HERE) + len(DIVIDER_FROM_HERE) + 1
        end_position = 0

    new_content = old_content[:start_position]
    new_content += "\n".join(blocks)
    if end_position:
        new_content += old_content[end_position:]
    new_content = new_content.strip() + "\n"

    if old_content != new_content:
        rst_file.write_text(new_content)
        click.secho(f"{rst_file} generated", fg="yellow")
        return 1

    click.secho(f"{rst_file} hasn't changed", fg="green")
    return 0


def generate_examples(filename: str) -> int:
    """Generate examples with hardcoded TOML content."""
    template = """
        .. _example-{link}:

        {header}
        {dashes}

        Contents of `{toml_file} <{base_url}v{version}/{toml_file}>`_:

        .. code-block::{language}

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
                base_url=GITHUB_BASE_URL,
                version=__version__,
                # Skip TOML with JSON inside, to avoid this error message:
                # nitpick/docs/examples.rst:193: WARNING: Could not lex literal_block as "toml". Highlighting skipped.
                language="" if "contains_json" in toml_content else " toml",
                toml_content="\n".join(indented_lines),
            )
        )

    rv = write_rst(filename, blocks)

    missing = SortedDict()
    for existing_toml_path in sorted(STYLES_DIR.glob("**/*.toml")):
        partial_name = str(existing_toml_path.relative_to(STYLES_DIR))
        if partial_name not in STYLE_MAPPING:
            missing[partial_name] = existing_toml_path.stem

    if missing:
        click.secho(
            f"ERROR: Add missing style files to the 'style_mapping' var in '{__file__}',"
            f" as file/header pairs. Example:",
            fg="red",
        )
        pprint(missing)
        sys.exit(1)
    return rv


def generate_plugins(filename: str) -> int:
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
    return write_rst(filename, blocks)


def generate_cli(filename: str) -> int:
    """Generate CLI docs."""
    template = """
        .. _cli_cmd{anchor}:

        {header}
        {dashes}
        {long}

        .. code-block::

        {help}
    """
    clean_template = dedent(template).strip()
    blocks = []

    for command, short, long in CLI_MAPPING:
        anchor = f"_{command}" if command else ""
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
                anchor=anchor, header=header, dashes="-" * len(header), long=dedent(long), help=indent(output, "    ")
            )
        )

    return write_rst(filename, blocks)


def generate_config(filename: str) -> int:
    """Generate config file names."""
    blocks = [f"{index + 1}. ``{config_file}``" for index, config_file in enumerate(CONFIG_FILES)]
    blocks.insert(0, "")
    blocks.append("")
    return write_rst(filename, blocks, divider_id="config-file")


if __name__ == "__main__":
    sys.exit(
        generate_config("configuration.rst")
        + generate_examples("examples.rst")
        + generate_cli("cli.rst")
        + generate_plugins("plugins.rst")
    )
