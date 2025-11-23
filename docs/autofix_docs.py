"""Autofix documentation files content from Python classes.

Run on the dev machine with "invoke doc", and commit on GitHub.
This also runs as a local pre-commit hook.

The ``include`` directive is not working on Read the Docs.
It doesn't recognise the "styles" dir anywhere (on the root, under "docs", under "_static"...).
Not even changing ``html_static_path`` on ``conf.py`` worked.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from importlib import import_module
from pathlib import Path
from subprocess import check_output  # nosec
from textwrap import dedent

import attr
import click
from slugify import slugify

from nitpick.constants import (
    CONFIG_FILES,
    DOT,
    EDITOR_CONFIG,
    PYTHON_PYLINTRC,
    PYTHON_SETUP_CFG,
    READ_THE_DOCS_URL,
    EmojiEnum,
)
from nitpick.core import Nitpick
from nitpick.style import BuiltinStyle, builtin_styles, repo_root

MD_DIVIDER_FROM_HERE = "<!-- auto-generated-from-here -->"
MD_DIVIDER_START = "<!-- auto-generated-start-{} -->"
MD_DIVIDER_END = "<!-- auto-generated-end-{} -->"

DOCS_DIR: Path = Path(__file__).parent.absolute()
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
    check: bool | int
    autofix: bool | int

    def __post_init__(self):
        """Warn about text that might render incorrectly."""
        if "`" in self.text:
            msg = f"Remove all backticks from the text: {self.text}"
            raise RuntimeError(msg)

    def __lt__(self, other: FileType) -> bool:
        """Sort instances.

        From the [docs](https://docs.python.org/3/howto/sorting.html#odd-and-ends):

        > It is easy to add a standard sort order to a class by defining an __lt__() method
        """
        return self.sort_key < other.sort_key

    @property
    def sort_key(self) -> str:
        """Sort key of this element."""
        return ("0" if self.text.startswith("Any") else "1") + self.text.casefold().replace(DOT, "")

    @property
    def text_with_url(self) -> str:
        """Text with URL in Markdown."""
        return f"[{self.text}]({self.url})" if self.url else self.text

    def _pretty(self, attribute: str) -> str:
        value = getattr(self, attribute)
        if value is True:
            return EmojiEnum.GREEN_CHECK.value
        if value is False:
            return EmojiEnum.X_RED_CROSS.value
        if value == 0:
            return EmojiEnum.QUESTION_MARK.value
        return f"[#{value}](https://github.com/andreoliwa/nitpick/issues/{value}) {EmojiEnum.CONSTRUCTION.value}"

    @property
    def check_str(self) -> str:
        """The check flag, as a string."""
        return self._pretty("check")

    @property
    def autofix_str(self) -> str:
        """The autofix flag, as a string."""
        return self._pretty("autofix")

    @property
    def row(self) -> tuple[str, str, str]:
        """Tuple for a table row."""
        return self.text_with_url, self.check_str, self.autofix_str


IMPLEMENTED_FILE_TYPES: set[FileType] = {
    FileType("Any INI file", f"{READ_THE_DOCS_URL}plugins.html#ini-files", True, True),
    FileType("Any JSON file", f"{READ_THE_DOCS_URL}plugins.html#json-files", True, True),
    FileType("Any plain text file", f"{READ_THE_DOCS_URL}plugins.html#text-files", True, False),
    FileType("Any TOML file", f"{READ_THE_DOCS_URL}plugins.html#toml-files", True, True),
    FileType("Any YAML file", f"{READ_THE_DOCS_URL}plugins.html#yaml-files", True, True),
    FileType(EDITOR_CONFIG, f"{READ_THE_DOCS_URL}library.html#any", True, True),
    FileType(PYTHON_PYLINTRC, f"{READ_THE_DOCS_URL}plugins.html#ini-files", True, True),
    FileType(PYTHON_SETUP_CFG, f"{READ_THE_DOCS_URL}plugins.html#ini-files", True, True),
}
PLANNED_FILE_TYPES: set[FileType] = {
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
    """A Markdown document file."""

    def __init__(self, filename: str) -> None:
        self.file: Path = (DOCS_DIR / filename).resolve(True)
        self.divider_start = MD_DIVIDER_START
        self.divider_end = MD_DIVIDER_END
        self.divider_from_here = MD_DIVIDER_FROM_HERE

    @staticmethod
    def _normalize_for_comparison(content: str) -> str:
        """Normalize content for comparison by removing whitespace differences.

        This allows us to compare content semantically, ignoring formatting differences
        that prettier might introduce (like table column alignment and separator row dashes).
        Uses slugify to normalize each line, which removes whitespace and special characters.
        """
        normalized_lines = []
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            # Use slugify to normalize the line (removes whitespace, lowercases, etc.)
            normalized = slugify(line)
            if normalized:
                normalized_lines.append(normalized)
        return "\n".join(normalized_lines)

    def write(self, lines: list[str], divider: str | None = None) -> int:
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

        # Extract the old section content for comparison
        old_section = old_content[start_position:end_position] if end_position else old_content[start_position:]
        new_section = "\n".join(lines)

        divider_message = f" (divider: {divider})" if divider else ""

        # Compare normalized versions to ignore whitespace differences (e.g., prettier formatting)
        if self._normalize_for_comparison(old_section) != self._normalize_for_comparison(new_section):
            new_content = old_content[:start_position]
            new_content += new_section
            if end_position:
                new_content += old_content[end_position:]
            new_content = new_content.strip() + "\n"

            self.file.write_text(new_content)
            click.secho(f"File {self.file}{divider_message} generated", fg="yellow")
            return 1

        click.secho(f"File {self.file}{divider_message} hasn't changed", fg="green")
        return 0


def write_plugins() -> int:
    """Write plugins.md with the docstrings from :py:class:`nitpick.plugins.base.NitpickPlugin` classes."""
    template = """
        ## {header} {{#{link}}}

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
            module = import_module(plugin_class.__module__)
            header = (module.__doc__ or "").strip(" .")

        blocks.append("")
        blocks.append(
            clean_template.format(
                link=slugify(plugin_class.__name__),
                header=header,
                description=dedent(plugin_class.__doc__).strip(),
            )
        )
    return DocFile("plugins.md").write(blocks)


def write_cli() -> int:
    """Write CLI docs."""
    template = """
        ## {header} {{#cli_cmd{anchor}}}

        {long}

        ```
        {help}
        ```
    """
    clean_template = dedent(template).strip()
    blocks = []

    for command, short, long in CLI_MAPPING:
        anchor = f"_{command}" if command else ""
        header = f"`{command}`: {short}" if command else short
        blocks.append("")
        parts = ["nitpick"]
        if command:
            parts.append(command)
        parts.append("--help")
        print(" ".join(parts))
        output = check_output(parts).decode().strip()  # noqa: S603
        blocks.append(clean_template.format(anchor=anchor, header=header, long=dedent(long).strip(), help=output))

    return DocFile("cli.md").write(blocks)


def write_config() -> int:
    """Write config file names."""
    blocks = [f"{index + 1}. ``{config_file}``" for index, config_file in enumerate(CONFIG_FILES)]
    blocks.insert(0, "")
    blocks.append("")
    return DocFile("configuration.md").write(blocks, divider="config-file")


def md_table(header: tuple[str, ...], rows: list[tuple[str, ...]]) -> list[str]:
    """Create a Markdown table from header and rows."""
    blocks = []
    # Header row
    blocks.append("| " + " | ".join(header) + " |")
    # Separator row
    blocks.append("| " + " | ".join(["---"] * len(header)) + " |")
    # Data rows
    blocks.extend("| " + " | ".join(row) + " |" for row in rows)
    return blocks


def write_readme(file_types: set[FileType], divider: str) -> int:
    """Write the README."""
    rows: list[tuple[str, ...]] = [file_type.row for file_type in sorted(file_types)]

    lines = md_table(("File type", "`nitpick check`", "`nitpick fix`"), rows)
    return DocFile("../README.md").write(lines, divider)


@attr.frozen(kw_only=True)
class StyleLibraryRow:  # pylint: disable=too-few-public-methods
    """Row in the style library."""

    style: str
    name: str


def _build_library(gitref: bool = True) -> list[str]:
    # pylint: disable=no-member
    library: dict[str, list[tuple]] = defaultdict(list)
    for path in sorted(builtin_styles()):  # type: Path
        style = BuiltinStyle.from_path(path)

        # When run with tox (invoke ci-build), the path starts with "site-packages"
        clean_root = path.relative_to(repo_root()).as_posix().replace("site-packages/", "src/")

        # Markdown link format with GitHub URL
        # Use macro syntax for version-aware URLs in docs, or relative path for README
        github_url = f"{{{{ github_url('{clean_root}') }}}}" if gitref else clean_root
        style_link = f"[{style.formatted}]({github_url})"
        name_link = f"[{style.name}]({style.url})" if style.url else style.name

        library[style.identify_tag].append(attr.astuple(StyleLibraryRow(style=style_link, name=name_link)))

    lines = []
    for tag, rows in library.items():
        lines.extend(["", f"## {tag}", ""])
        lines.extend(
            md_table(
                (
                    "Style URL",
                    "Description",
                ),
                rows,
            )
        )
    return lines


def write_style_library(divider: str) -> int:
    """Write the style library table."""
    lines = _build_library(gitref=False)
    rv = DocFile("../README.md").write(lines, divider)

    lines = _build_library(gitref=True)
    rv += DocFile("library.md").write(lines, divider)
    return rv


def copy_quickstart() -> int:
    """Copy the quickstart section to README.md."""
    quickstart_file = DOCS_DIR / "quickstart.md"
    content = quickstart_file.read_text().replace("{{ github_url('nitpick-style.toml') }}", "nitpick-style.toml")
    lines = content.splitlines()
    return DocFile("../README.md").write(lines, "quickstart")


if __name__ == "__main__":
    sys.exit(
        write_readme(IMPLEMENTED_FILE_TYPES, "implemented")
        + write_readme(PLANNED_FILE_TYPES, "planned")
        + write_style_library("style-library")
        + copy_quickstart()
        + write_config()
        + write_plugins()
        + write_cli()
    )
