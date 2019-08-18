"""Generate defaults.rst with the TOML styles, on the dev machine during "make", to be committed on GitHub.

The ``include`` directive is not working on ReadTheDocs.
It doesn't recognise the "styles" dir anywhere (on the root, under "docs", under "_static"...).
Not even changing ``html_static_path`` on ``conf.py`` worked.
"""
from pathlib import Path
from pprint import pprint
from textwrap import dedent

import click
from sortedcontainers import SortedDict

from nitpick import __version__

mapping = SortedDict(
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
        "python35-36-37.toml": "Python 3.5, 3.6 or 3.7",
        "python36-37.toml": "Python 3.6 or 3.7",
        "python36.toml": "Python 3.6",
        "python37.toml": "Python 3.7",
    }
)

divider = ".. _toml_files:"
docs_dir = Path(__file__).parent.absolute()  # type: Path
styles_dir = docs_dir.parent / "styles"  # type: Path
defaults_rst = docs_dir / "defaults.rst"  # type: Path
base_url = "https://raw.githubusercontent.com/andreoliwa/nitpick"


def generate_defaults_rst():
    """Generate defaults.rst with hardcoded TOML content."""
    template = """
        {header}
        {dashes}

        Content of `{toml_file} <{url}>`_:

        .. code-block:: toml

        {toml_content}
    """
    clean_template = dedent(template).strip()
    blocks = []
    for toml_file, header in mapping.items():
        style_path = styles_dir / toml_file
        toml_content = style_path.read_text().strip()
        if not toml_content:
            # Skip empty TOML styles
            continue

        base_name = str(style_path.relative_to(styles_dir.parent))
        indented_lines = [("    " + line.rstrip()).rstrip() for line in toml_content.split("\n")]
        blocks.append("")
        blocks.append(
            clean_template.format(
                header=header,
                dashes="-" * len(header),
                toml_file=base_name,
                url="{}/v{}/{}".format(base_url, __version__, base_name),
                toml_content="\n".join(indented_lines),
            )
        )

    old_content = defaults_rst.read_text()
    cut_position = old_content.index(divider)
    new_content = old_content[: cut_position + len(divider) + 1]
    new_content += "\n".join(blocks)
    defaults_rst.write_text(new_content.strip() + "\n")
    click.secho("{} generated with TOML styles".format(defaults_rst), fg="green")

    missing = SortedDict()
    for existing_toml_path in sorted(styles_dir.glob("**/*.toml")):
        partial_name = str(existing_toml_path.relative_to(styles_dir))
        if partial_name not in mapping:
            missing[partial_name] = existing_toml_path.stem

    if missing:
        click.secho(
            "ERROR: Add missing style files to the 'mapping' var in '{}', as file/header pairs. Example:".format(
                __file__
            ),
            fg="red",
        )
        pprint(missing)
        exit(1)


if __name__ == "__main__":
    generate_defaults_rst()
