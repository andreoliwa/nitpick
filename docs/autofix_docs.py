"""Autofix documentation files content from Python classes.

Run on the dev machine with "invoke doc", and commit on GitHub.
This also runs as a local pre-commit hook.

The ``include`` directive is not working on Read the Docs.
It doesn't recognise the "styles" dir anywhere (on the root, under "docs", under "_static"...).
Not even changing ``html_static_path`` on ``conf.py`` worked.
"""
import sys
from collections import defaultdict
from importlib import import_module
from pathlib import Path
from pprint import pprint
from subprocess import check_output  # nosec
from textwrap import dedent, indent
from typing import Dict, List, Set, Tuple, Union

import attr
import click
from slugify import slugify
from sortedcontainers import SortedDict

from nitpick import PROJECT_NAME, __version__
from nitpick.constants import CONFIG_FILES, DOT, EDITOR_CONFIG, PROJECT_OWNER, PYLINTRC, READ_THE_DOCS_URL, SETUP_CFG
from nitpick.core import Nitpick
from nitpick.style.fetchers.github import GitHubURL
from nitpick.style.fetchers.pypackage import BuiltinStyle, builtin_styles

RST_DIVIDER_FROM_HERE = ".. auto-generated-from-here"
RST_DIVIDER_START = ".. auto-generated-start-{}"
RST_DIVIDER_END = ".. auto-generated-end-{}"

MD_DIVIDER_START = "<!-- auto-generated-start-{} -->"
MD_DIVIDER_END = "<!-- auto-generated-end-{} -->"

DOCS_DIR: Path = Path(__file__).parent.absolute()
STYLES_DIR: Path = DOCS_DIR.parent / "src" / "nitpick" / "resources"

# FIXME: add name and URL to the style itself [nitpick.meta], and generate this mapping instead of editing manually
STYLE_MAPPING = SortedDict(
    {
        "python/absent.toml": "Absent files",
        "python/black.toml": "black_",
        "any/editorconfig.toml": "EditorConfig_",
        "python/flake8.toml": "flake8_",
        "python/ipython.toml": "IPython_",
        "python/isort.toml": "isort_",
        "python/mypy.toml": "mypy_",
        "javascript/package-json.toml": "package.json_",
        "python/poetry.toml": "Poetry_",
        "shell/bashate.toml": "bashate_",
        "any/commitizen.toml": "commitizen_",
        "any/commitlint.toml": "commitlint_",
        "python/pre-commit-hooks.toml": "pre-commit_ hooks for Python",
        "python/pylint.toml": "Pylint_",
        "python/37.toml": "Python 3.7",
        "python/38.toml": "Python 3.8",
        "python/39.toml": "Python 3.9",
        "python/310.toml": "Python 3.10",
        "python/tox.toml": "tox_",
        "python/stable.toml": "Python (stable version)",
        "python/readthedocs.toml": "ReadTheDocs_",
        "any/git-legal.toml": "git-legal_",
        "any/pre-commit-hooks.toml": "pre-commit_ hooks for any language",
        "any/markdownlint.toml": "markdownlint_",
        "python/bandit.toml": "bandit_",
        "any/codeclimate.toml": "codeclimate_",
        "python/radon.toml": "radon_",
        "python/sonar-python.toml": "sonar-python_",
        "shell/shellcheck.toml": "shellcheck_",
        "python/github-workflow.toml": "GitHub Workflow (Python)",
        "python/autoflake.toml": "autoflake_",
        "any/prettier.toml": "Prettier_",
    }
)
CLI_MAPPING = [
    ("", "Main options", ""),
    (
        "fix",
        "Modify files directly",
        """
        At the end of execution, this command displays:

        - the number of fixed violations;
        - the number of violations that have to be changed manually.
        """,
    ),
    ("check", "Don't modify, just print the differences", ""),
    ("ls", "List configures files", ""),
    ("init", "Initialise a configuration file", ""),
]


@attr.frozen()
class FileType:
    """A file type handled by Nitpick."""

    text: str
    url: str
    check: Union[bool, int]
    autofix: Union[bool, int]

    def __post_init__(self):
        """Warn about text that might render incorrectly."""
        if "`" in self.text:
            raise RuntimeError(f"Remove all backticks from the text: {self.text}")

    def __lt__(self, other: "FileType") -> bool:
        """Sort instances.

        From the `docs <https://docs.python.org/3/howto/sorting.html#odd-and-ends>`_:

        > It is easy to add a standard sort order to a class by defining an __lt__() method
        """
        return self.sort_key < other.sort_key

    @property
    def sort_key(self) -> str:
        """Sort key of this element."""
        return ("0" if self.text.startswith("Any") else "1") + self.text.casefold().replace(DOT, "")

    @property
    def text_with_url(self) -> str:
        """Text with URL in reStructuredText."""
        return f"`{self.text} <{self.url}>`_" if self.url else self.text

    def _pretty(self, attribute: str) -> str:
        value = getattr(self, attribute)
        if value is True:
            return "✅"
        if value is False:
            return "❌"
        if value == 0:
            return "❓"
        return f"`#{value} <https://github.com/andreoliwa/nitpick/issues/{value}>`_ 🚧"

    @property
    def check_str(self) -> str:
        """The check flag, as a string."""
        return self._pretty("check")

    @property
    def autofix_str(self) -> str:
        """The autofix flag, as a string."""
        return self._pretty("autofix")

    @property
    def row(self) -> Tuple[str, str, str]:
        """Tuple for a table row."""
        return self.text_with_url, self.check_str, self.autofix_str


IMPLEMENTED_FILE_TYPES: Set[FileType] = {
    FileType("Any INI file", f"{READ_THE_DOCS_URL}plugins.html#ini-files", True, True),
    FileType("Any JSON file", f"{READ_THE_DOCS_URL}plugins.html#json-files", True, True),
    FileType("Any plain text file", f"{READ_THE_DOCS_URL}plugins.html#text-files", True, False),
    FileType("Any TOML file", f"{READ_THE_DOCS_URL}plugins.html#toml-files", True, True),
    FileType("Any YAML file", f"{READ_THE_DOCS_URL}plugins.html#yaml-files", True, True),
    FileType(EDITOR_CONFIG, f"{READ_THE_DOCS_URL}examples.html#example-editorconfig", True, True),
    FileType(PYLINTRC, f"{READ_THE_DOCS_URL}plugins.html#ini-files", True, True),
    FileType(SETUP_CFG, f"{READ_THE_DOCS_URL}plugins.html#ini-files", True, True),
}
PLANNED_FILE_TYPES: Set[FileType] = {
    FileType("Any Markdown file", "", 280, 0),
    FileType("Any Terraform file", "", 318, 0),
    FileType(".dockerignore", "", 8, 8),
    FileType(".gitignore", "", 8, 8),
    FileType("Dockerfile", "", 272, 272),
    FileType("Jenkinsfile", "", 278, 0),
    FileType("Makefile", "", 277, 0),
}

nit = Nitpick.singleton().init()


class DocFile:  # pylint: disable=too-few-public-methods
    """A document file (REST or Markdown)."""

    def __init__(self, filename: str) -> None:
        self.file: Path = (DOCS_DIR / filename).resolve(True)
        if self.file.suffix == ".md":
            self.divider_start = MD_DIVIDER_START
            self.divider_end = MD_DIVIDER_END
            self.divider_from_here = MD_DIVIDER_START
        else:
            self.divider_start = RST_DIVIDER_START
            self.divider_end = RST_DIVIDER_END
            self.divider_from_here = RST_DIVIDER_FROM_HERE

    def write(self, lines: List[str], divider: str = None) -> int:
        """Write content to the file."""
        old_content = self.file.read_text()
        if divider:
            start_marker = self.divider_start.format(divider)
            end_marker = self.divider_end.format(divider)
            start_position = old_content.index(start_marker) + len(start_marker) + 1
            end_position = old_content.index(end_marker) - 1
        else:
            start_position = old_content.index(self.divider_from_here) + len(self.divider_from_here) + 1
            end_position = 0

        new_content = old_content[:start_position]
        new_content += "\n".join(lines)
        if end_position:
            new_content += old_content[end_position:]
        new_content = new_content.strip() + "\n"

        divider_message = f" (divider: {divider})" if divider else ""
        if old_content != new_content:
            self.file.write_text(new_content)
            click.secho(f"File {self.file}{divider_message} generated", fg="yellow")
            return 1

        click.secho(f"File {self.file}{divider_message} hasn't changed", fg="green")
        return 0


def write_examples() -> int:
    """Write examples with hardcoded TOML content."""
    template = """
        .. _example-{link}:

        {header}
        {dashes}

        Contents of `{toml_file} <{url}>`_:

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
                url=GitHubURL(PROJECT_OWNER, PROJECT_NAME, f"v{__version__}", base_name, "").url,
                # Skip TOML with JSON inside, to avoid this error message:
                # nitpick/docs/examples.rst:193: WARNING: Could not lex literal_block as "toml". Highlighting skipped.
                language="" if "contains_json" in toml_content else " toml",
                toml_content="\n".join(indented_lines),
            )
        )

    rv = DocFile("examples.rst").write(blocks)

    missing = SortedDict()
    for existing_toml_path in sorted(STYLES_DIR.glob("**/*.toml")):
        partial_name = str(existing_toml_path.relative_to(STYLES_DIR))
        if partial_name not in STYLE_MAPPING:
            missing[partial_name] = existing_toml_path.stem

    if missing:
        click.secho(
            f"ERROR: Add missing style files to the 'STYLE_MAPPING' var in '{__file__}',"
            f" as file/header pairs. Example:",
            fg="red",
        )
        pprint(missing)
        sys.exit(1)
    return rv


def write_plugins() -> int:
    """Write plugins.rst with the docstrings from :py:class:`nitpick.plugins.base.NitpickPlugin` classes."""
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
    return DocFile("plugins.rst").write(blocks)


def write_cli() -> int:
    """Write CLI docs."""
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

    return DocFile("cli.rst").write(blocks)


def write_config() -> int:
    """Write config file names."""
    blocks = [f"{index + 1}. ``{config_file}``" for index, config_file in enumerate(CONFIG_FILES)]
    blocks.insert(0, "")
    blocks.append("")
    return DocFile("configuration.rst").write(blocks, divider="config-file")


def rst_table(header: Tuple[str, ...], rows: List[Tuple[str, ...]]) -> List[str]:
    """Create a ReST table from header and rows."""
    blocks = [".. list-table::\n   :header-rows: 1\n"]
    num_columns = len(header)
    for row in [header] + rows:
        template = ("*" + " - {}\n " * num_columns).rstrip()
        blocks.append(indent(template.format(*row), "   "))
    return blocks


def write_readme(file_types: Set[FileType], divider: str) -> int:
    """Write the README."""
    # TODO: quickstart.rst has some parts of README.rst as a copy/paste/change
    rows: List[Tuple[str, ...]] = []
    for file_type in sorted(file_types):
        rows.append(file_type.row)

    lines = rst_table(("File type", "``nitpick check``", "``nitpick fix``"), rows)
    return DocFile("../README.rst").write(lines, divider)


@attr.frozen(kw_only=True)
class StyleLibraryRow:  # pylint: disable=too-few-public-methods
    """Row in the style library."""

    style: str
    name: str


def write_style_library(divider: str) -> int:
    """Write the style library table."""
    # pylint: disable=no-member
    library: Dict[str, List[Tuple]] = defaultdict(list)
    for path in sorted(builtin_styles()):  # type: Path
        style = BuiltinStyle.from_path(path)
        row = StyleLibraryRow(
            style=f"``{style.py_pretty_url}`` (`link <{style.from_repo_root}>`_)",
            name=f"`{style.name} <{style.url}>`_" if style.url else style.name,
        )
        library[style.identify_tag].append(attr.astuple(row))

    lines = []
    for tag, rows in library.items():
        lines.extend(["", tag, "~" * len(tag), ""])
        lines.extend(
            rst_table(
                (
                    "Style URL",
                    "Description",
                ),
                rows,
            )
        )
    return DocFile("../README.rst").write(lines, divider)


if __name__ == "__main__":
    sys.exit(
        write_readme(IMPLEMENTED_FILE_TYPES, "implemented")
        + write_readme(PLANNED_FILE_TYPES, "planned")
        + write_style_library("style-library")
        + write_config()
        + write_examples()  # FIXME: the style library replaces this
        + write_plugins()
        + write_cli()
    )
