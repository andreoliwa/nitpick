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
from loguru import logger
from tomlkit import items

from nitpick import tomlkit_ext
from nitpick.constants import (
    CONFIG_KEY_DONT_SUGGEST,
    CONFIG_KEY_STYLE,
    CONFIG_KEY_TOOL,
    CONFIG_TOOL_NITPICK_KEY,
    PROJECT_NAME,
    EmojiEnum,
    OptionEnum,
)
from nitpick.core import Nitpick
from nitpick.exceptions import QuitComplainingError
from nitpick.generic import relative_to_current_dir
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
    "--fix",
    "-f",
    is_flag=True,
    default=False,
    help="Autofix the files changed by the command; otherwise, just print what would be done",
)
@click.option(
    "--suggest",
    "-s",
    is_flag=True,
    default=False,
    help="Suggest styles based on the files in the project root (skipping Git ignored files)",
)
@click.argument("style_urls", nargs=-1)
# TODO(AA): fix complexity and too-many-locals after writing tests
def init(  # noqa: C901 # pylint: disable=too-many-locals
    context,
    fix: bool,  # pylint: disable=redefined-outer-name
    suggest: bool,
    style_urls: list[str],
) -> None:
    """Create or update the [tool.nitpick] table in the configuration file."""
    nit = get_nitpick(context)
    path = nit.project.config_file_or_default()
    doc = tomlkit_ext.load(path)
    tool_nitpick_table: tomlkit_ext.Table | None = doc.get(CONFIG_TOOL_NITPICK_KEY)
    if tool_nitpick_table and not fix:
        click.secho(
            f"The config file {path.name!r} already has a [{CONFIG_TOOL_NITPICK_KEY}] table."
            " Use --force to override it.",
            fg="yellow",
        )
        return
    if not style_urls and not suggest:
        click.secho(
            "Nothing to do. 😴 Either pass at least one style URL"
            " or use --suggest to add styles based on the files in the project root"
            " (you can do both at the same time).",
            fg="yellow",
        )
        return

    # Convert tuple to list, so we can add styles to it
    style_urls = list(style_urls)

    if suggest:
        style_urls.extend(nit.project.suggest_styles())

    if not tool_nitpick_table:
        super_table = tomlkit.table(True)
        nitpick_table = tomlkit.table()
        nitpick_table.update({CONFIG_KEY_STYLE: []})
        super_table.append(PROJECT_NAME, nitpick_table)
        doc.append(CONFIG_KEY_TOOL, super_table)
        tool_nitpick_table = doc.get(CONFIG_TOOL_NITPICK_KEY)

    style_array: items.Array = tool_nitpick_table.get(CONFIG_KEY_STYLE)
    if style_array is None:
        style_array = tomlkit.array()
        tool_nitpick_table.add(CONFIG_KEY_STYLE, style_array)

    ignore_styles_array: items.Array = tool_nitpick_table.get(CONFIG_KEY_DONT_SUGGEST)
    if ignore_styles_array is None:
        ignore_styles_array = tomlkit.array()
        if suggest:
            # Create the ignored styles array only when suggesting styles
            tool_nitpick_table.add(CONFIG_KEY_DONT_SUGGEST, ignore_styles_array)

    added_count = 0
    for style_url in style_urls:
        if style_url in style_array or style_url in ignore_styles_array:
            continue
        added_count += 1
        style_array.add_line(style_url, indent="  ")

    if suggest:
        from nitpick import __version__  # pylint: disable=import-outside-toplevel

        tomlkit_ext.update_comment_before(
            tool_nitpick_table,
            CONFIG_KEY_STYLE,
            PROJECT_NAME,
            f"""
            (auto-generated by "nitpick init --suggest" {__version__})
            Styles added to the Nitpick Style Library will be appended at the end of the {CONFIG_KEY_STYLE!r} key.
            If you don't want a style, move it to the {CONFIG_KEY_DONT_SUGGEST!r} key.
            """,
        )

    if added_count == 0:
        click.echo(
            f"All done! {EmojiEnum.STAR_CAKE.value} [{CONFIG_TOOL_NITPICK_KEY}] table left unchanged in {path.name!r}"
        )
        return

    # TODO(AA): without --force, only print what would be done
    path.write_text(tomlkit.dumps(doc), encoding="UTF-8")
    verb = "updated" if fix else "created"
    click.secho(
        f"The [{CONFIG_TOOL_NITPICK_KEY}] table was {verb} in {path.name!r}:"
        f" {added_count} styles added. {EmojiEnum.STAR_CAKE.value}",
        fg="green",
    )
    raise Exit(1)  # Needed to be used as a pre-commit hook
