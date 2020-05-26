"""Generate .rst files content from Python classes. Run on the dev machine with "make", and commit on GitHub.

The ``include`` directive is not working on Read the Docs.
It doesn't recognise the "styles" dir anywhere (on the root, under "docs", under "_static"...).
Not even changing ``html_static_path`` on ``conf.py`` worked.
"""
import sys
from importlib import import_module
from pathlib import Path
from pprint import pprint
from textwrap import dedent
from typing import List

import click
from slugify import slugify
from sortedcontainers import SortedDict

from nitpick.constants import RAW_GITHUB_CONTENT_BASE_URL
from nitpick.files.base import BaseFile
from nitpick.files.json import JSONFile
from nitpick.files.pre_commit import PreCommitFile
from nitpick.files.pyproject_toml import PyProjectTomlFile
from nitpick.files.setup_cfg import SetupCfgFile
from nitpick.generic import get_subclasses

style_mapping = SortedDict(
    {
        "black.toml": "black_",
        "flake8.toml": "flake8_",
        "isort.toml": "isort_",
        "mypy.toml": "mypy_",
        "absent-files.toml": "Absent files",
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
        "python35-36-37-38.toml": "Python 3.5, 3.6, 3.7 to 3.8",
        "python36-37.toml": "Python 3.6 or 3.7",
        "python36.toml": "Python 3.6",
        "python37.toml": "Python 3.7",
    }
)
file_classes = [PyProjectTomlFile, SetupCfgFile, PreCommitFile, JSONFile]

divider = ".. auto-generated-from-here"
docs_dir = Path(__file__).parent.absolute()  # type: Path
styles_dir = docs_dir.parent / "styles"  # type: Path


def write_rst(rst_file: Path, blocks: List[str]):
    """Write content to the .rst file."""
    old_content = rst_file.read_text()
    cut_position = old_content.index(divider)
    new_content = old_content[: cut_position + len(divider) + 1]
    new_content += "\n".join(blocks)
    rst_file.write_text(new_content.strip() + "\n")
    click.secho("{} generated".format(rst_file), fg="green")


def generate_defaults_rst():
    """Generate defaults.rst with hardcoded TOML content."""
    rst_file = docs_dir / "defaults.rst"  # type: Path

    template = """
        .. _default-{link}:

        {header}
        {dashes}

        Content of `{toml_file} <{base_url}/develop/{toml_file}>`_:

        .. code-block:: toml

        {toml_content}
    """
    clean_template = dedent(template).strip()
    blocks = []
    for toml_file, header in style_mapping.items():
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
                link=slugify(header),
                header=header,
                dashes="-" * len(header),
                toml_file=base_name,
                base_url=RAW_GITHUB_CONTENT_BASE_URL,
                toml_content="\n".join(indented_lines),
            )
        )

    write_rst(rst_file, blocks)

    missing = SortedDict()
    for existing_toml_path in sorted(styles_dir.glob("**/*.toml")):
        partial_name = str(existing_toml_path.relative_to(styles_dir))
        if partial_name not in style_mapping:
            missing[partial_name] = existing_toml_path.stem

    if missing:
        click.secho(
            "ERROR: Add missing style files to the 'style_mapping' var in '{}', as file/header pairs. Example:".format(
                __file__
            ),
            fg="red",
        )
        pprint(missing)
        sys.exit(1)


def generate_config_files_rst():
    """Generate config_files.rst with the docstrings from BaseFile classes."""
    rst_file = docs_dir / "config_files.rst"  # type: Path

    template = """
        .. _{link}:

        {header}
        {dashes}

        {description}
    """
    clean_template = dedent(template).strip()
    blocks = []
    for file_class in file_classes:
        header = file_class.file_name
        if not header:
            # module_name = file_class.__module__
            module = import_module(file_class.__module__)
            header = module.__doc__.strip(" .")

        stripped_lines = [line.strip() for line in file_class.__doc__.split("\n")]

        blocks.append("")
        blocks.append(
            clean_template.format(
                link=slugify(file_class.__name__),
                header=header,
                dashes="-" * len(header),
                description="\n".join(stripped_lines).strip(),
            )
        )
    write_rst(rst_file, blocks)

    existing = set(get_subclasses(BaseFile))
    documented = set(file_classes)
    something_missing = existing - documented
    for missing_class in something_missing:
        click.secho(
            "ERROR: Add missing base file {} to the 'file_classes' var in '{}'.".format(
                missing_class.__name__, __file__
            ),
            fg="red",
        )
    if something_missing:
        sys.exit(1)


if __name__ == "__main__":
    generate_defaults_rst()
    generate_config_files_rst()
