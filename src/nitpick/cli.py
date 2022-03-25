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
from click.exceptions import Exit
from loguru import logger

from nitpick.blender import TomlDoc
from nitpick.constants import PROJECT_NAME, TOOL_KEY, TOOL_NITPICK_KEY
from nitpick.core import Nitpick
from nitpick.enums import OptionEnum
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
def nitpick_cli(project: Path = None, offline=False):  # pylint: disable=unused-argument
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
@click.argument("style_urls", nargs=-1)
def init(context, style_urls):
    """Create a [tool.nitpick] section in the configuration file if it doesn't exist already."""
    nit = get_nitpick(context)
    config = nit.project.read_configuration()

    if config.file and PROJECT_NAME in TomlDoc(path=config.file).as_object.get(TOOL_KEY, {}):
        click.secho(f"The config file {config.file.name} already has a [{TOOL_NITPICK_KEY}] section.", fg="yellow")
        raise Exit(1)

    nit.project.create_configuration(config, *style_urls)
    click.secho(f"A [{TOOL_NITPICK_KEY}] section was created in the config file: {config.file.name}", fg="green")
