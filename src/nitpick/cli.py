"""Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

You might be tempted to import things from __main__ later, but that will cause
problems: the code will get executed twice:

- When you run `python -mnitpick` python will execute ``__main__.py`` as a script.
    That means there won't be any ``nitpick.__main__`` in ``sys.modules``.
- When you import __main__ it will get executed again (as a module) because
    there's no ``nitpick.__main__`` in ``sys.modules``.

Also see (1) from https://click.palletsprojects.com/en/5.x/setuptools/#setuptools-integration
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import click
import tomlkit
from click.exceptions import Exit
from identify import identify
from loguru import logger
from tomlkit import items

from nitpick import __version__, tomlkit_ext
from nitpick.constants import (
    ANY_BUILTIN_STYLE,
    CONFIG_KEY_IGNORE_STYLES,
    CONFIG_KEY_STYLE,
    CONFIG_TOOL_NITPICK_KEY,
    PROJECT_NAME,
)
from nitpick.core import Nitpick
from nitpick.enums import OptionEnum
from nitpick.exceptions import QuitComplainingError
from nitpick.generic import glob_non_ignored_files, relative_to_current_dir
from nitpick.style.fetchers.pypackage import BuiltinStyle, builtin_styles
from nitpick.tomlkit_ext import update_comment_before
from nitpick.violations import Reporter

VERBOSE_OPTION = click.option(
    "--verbose", "-v", count=True, default=False, help="Increase logging verbosity (-v = INFO, -vv = DEBUG)"
)
FILES_ARGUMENT = click.argument("files", nargs=-1)


@click.group()
@click.option(
    "--project",
    "-p",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, resolve_path=True),
    help="Path to project root",
)
@click.option(
    f"--{OptionEnum.OFFLINE.name.lower()}",  # pylint: disable=no-member
    is_flag=True,
    default=False,
    help=OptionEnum.OFFLINE.value,
)
@click.version_option()
def nitpick_cli(project: Path | None = None, offline=False):  # pylint: disable=unused-argument # noqa: ARG001
    """Enforce the same settings across multiple language-independent projects."""


def get_nitpick(context: click.Context) -> Nitpick:
    """Create a Nitpick instance from the click context parameters."""
    project = None
    offline = False
    if context.parent:
        project = context.parent.params["project"]
        offline = context.parent.params["offline"]
    project_root: Path | None = Path(project) if project else None
    return Nitpick.singleton().init(project_root, offline)


def common_fix_or_check(context, verbose: int, files, check_only: bool) -> None:
    """Common CLI code for both "fix" and "check" commands."""
    if verbose:
        level = logging.INFO if verbose == 1 else logging.DEBUG

        # https://loguru.readthedocs.io/en/stable/resources/recipes.html#changing-the-level-of-an-existing-handler
        # https://github.com/Delgan/loguru/issues/138#issuecomment-525594566
        logger.remove()
        logger.add(sys.stderr, level=logging.getLevelName(level))

        logger.enable(PROJECT_NAME)

    nit = get_nitpick(context)
    try:
        for fuss in nit.run(*files, autofix=not check_only):
            nit.echo(fuss.pretty)
    except QuitComplainingError as err:
        for fuss in err.violations:
            click.echo(fuss.pretty)
        raise Exit(2) from err

    click.secho(Reporter.get_counts())
    if Reporter.manual or Reporter.fixed:
        raise Exit(1)


@nitpick_cli.command()
@click.pass_context
@VERBOSE_OPTION
@FILES_ARGUMENT
def fix(context, verbose, files):
    """Fix files, modifying them directly.

    You can use partial and multiple file names in the FILES argument.
    """
    common_fix_or_check(context, verbose, files, False)


@nitpick_cli.command()
@click.pass_context
@VERBOSE_OPTION
@FILES_ARGUMENT
def check(context, verbose, files):
    """Don't modify files, just print the differences.

    Return code 0 means nothing would change. Return code 1 means some files would be modified.
    You can use partial and multiple file names in the FILES argument.
    """
    common_fix_or_check(context, verbose, files, True)


@nitpick_cli.command()
@click.pass_context
@FILES_ARGUMENT
def ls(context, files):  # pylint: disable=invalid-name
    """List of files configured in the Nitpick style.

    Display existing files in green and absent files in red.
    You can use partial and multiple file names in the FILES argument.
    """
    nit = get_nitpick(context)
    try:
        violations = list(nit.project.merge_styles(nit.offline))
        error_exit_code = 1
    except QuitComplainingError as err:
        violations = err.violations
        error_exit_code = 2
    if violations:
        for fuss in violations:
            click.echo(fuss.pretty)
        raise Exit(error_exit_code)  # TODO: test: ls with invalid style

    # TODO: test: configured_files() API
    for file in nit.configured_files(*files):
        click.secho(relative_to_current_dir(file), fg="green" if file.exists() else "red")


@nitpick_cli.command()
@click.pass_context
@click.option(
    "--force",
    "-f",
    is_flag=True,
    default=False,
    help="Overwrite the section if it already exists",
)
@click.argument("style_urls", nargs=-1)
def init(context, force: bool, style_urls: list[str]) -> None:
    """Create a [tool.nitpick] section in the configuration file."""
    nit = get_nitpick(context)
    # TODO(AA): test --force flag
    path = nit.project.config_file_or_default()
    doc = tomlkit_ext.load(path)
    tool_nitpick: tomlkit_ext.Table | None = doc.get(CONFIG_TOOL_NITPICK_KEY)
    if not tool_nitpick:
        if not force:
            click.secho(
                f"The config file {path.name!r} already has a [{CONFIG_TOOL_NITPICK_KEY}] section.", fg="yellow"
            )
            raise Exit(1)
        # TODO(AA): test this case
        tool_nitpick = doc.add(tomlkit.table())

    if not style_urls:
        tags: set[str] = {ANY_BUILTIN_STYLE}
        for project_file_path in glob_non_ignored_files(nit.project.root):
            tags.update(identify.tags_from_path(str(project_file_path)))
        suggested_styles: set[str] = set()
        for style_path in builtin_styles():
            builtin_style = BuiltinStyle.from_path(style_path)
            if builtin_style.identify_tag in tags:
                suggested_styles.add(builtin_style.py_url_without_ext.url)
        style_urls = sorted(suggested_styles)

    style_array: items.Array = tool_nitpick.get(CONFIG_KEY_STYLE)
    if not style_array:
        # TODO(AA): test this case
        style_array = tool_nitpick.append(CONFIG_KEY_STYLE, tomlkit.array())

    for style_url in style_urls:
        if style_url in style_array:
            continue
        style_array.add_line(style_url, indent="  ")

    update_comment_before(
        tool_nitpick,
        CONFIG_KEY_STYLE,
        PROJECT_NAME,
        f"""
        (auto-generated by "nitpick init" {__version__})
        New styles added to the Nitpick library are automatically added here.
        If you don't want a style, move it manually to the {CONFIG_KEY_IGNORE_STYLES!r} key.
        """,
    )

    # TODO(AA): add an empty ignored styles with CONFIG_KEY_IGNORE_STYLES
    #  Add here the full path of the styles you want "nitpick init" to ignore

    path.write_text(tomlkit.dumps(doc), encoding="UTF-8")
    verb = "updated" if force else "created"
    click.secho(
        f"The [{CONFIG_TOOL_NITPICK_KEY}] table was {verb} in the TOML config file {path.name!r}"
        f" (keys: {CONFIG_KEY_STYLE!r}, {CONFIG_KEY_IGNORE_STYLES!r})",
        fg="green",
    )
