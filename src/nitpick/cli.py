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

from nitpick import tomlkit_ext
from nitpick.constants import (
    CONFIG_KEY_IGNORE_STYLES,
    CONFIG_KEY_STYLE,
    CONFIG_TOOL_NITPICK_KEY,
    PROJECT_NAME,
    EmojiEnum,
    Flake8OptionEnum,
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
    f"--{Flake8OptionEnum.OFFLINE.name.lower()}",  # pylint: disable=no-member
    is_flag=True,
    default=False,
    help=Flake8OptionEnum.OFFLINE.value,
)
@click.version_option()
def nitpick_cli(project: Path | None = None, offline=False):  # pylint: disable=unused-argument
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
    help="Suggest styles based on the extension of project files (skipping Git ignored files)",
)
@click.option(
    "--library",
    "-l",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, resolve_path=True),
    help="Library dir to scan for style files (implies --suggest); if not provided, uses the built-in style library",
)
@click.argument("style_urls", nargs=-1)
def init(
    context,
    fix: bool,  # pylint: disable=redefined-outer-name
    suggest: bool,
    library: str | None,
    style_urls: list[str],
) -> None:
    """Create or update the [tool.nitpick] table in the configuration file."""
    # If a library is provided, it implies --suggest
    if library:
        suggest = True

    if not style_urls and not suggest:
        click.secho(
            f"Nothing to do. {EmojiEnum.SLEEPY_FACE.value} Either pass at least one style URL"
            " or use --suggest to add styles based on the files in the project root"
            " (you can do both at the same time).",
            fg="yellow",
        )
        return

    nit = get_nitpick(context)
    config = nit.project.read_configuration()

    # Convert tuple to list, so we can add styles to it
    style_urls = list(style_urls)
    if suggest:
        from nitpick import __version__  # pylint: disable=import-outside-toplevel  # noqa: PLC0415

        # Create the ignored styles array only when suggesting styles
        if CONFIG_KEY_IGNORE_STYLES not in config.table:
            config.table.add(CONFIG_KEY_IGNORE_STYLES, config.dont_suggest)

        style_urls.extend(nit.project.suggest_styles(library))
        tomlkit_ext.update_comment_before(
            config.table,
            CONFIG_KEY_STYLE,
            PROJECT_NAME,
            f"""
            (auto-generated by "nitpick init --suggest" {__version__})
            Styles added to the Nitpick Style Library will be appended to the end of the {CONFIG_KEY_STYLE!r} key.
            If you don't want a style, move it to the {CONFIG_KEY_IGNORE_STYLES!r} key.
            """,
        )

    new_styles = []
    for style_url in style_urls:
        if style_url in config.styles or style_url in config.dont_suggest:
            continue
        new_styles.append(style_url)
        config.styles.add_line(style_url, indent="  ")
    if not new_styles:
        click.echo(
            f"All done! {EmojiEnum.STAR_CAKE.value} [{CONFIG_TOOL_NITPICK_KEY}] table left unchanged in {config.file.name!r}"
        )
        return

    click.echo("New styles:")
    for style in new_styles:
        click.echo(f"- {style}")
    count = len(new_styles)
    message = f"{count} style{'s' if count > 1 else ''}"

    if not fix:
        click.secho(
            f"Use --fix to append {message} to the [{CONFIG_TOOL_NITPICK_KEY}]"
            f" table in the config file {config.file.name!r}.",
            fg="yellow",
        )
        return

    config.file.write_text(tomlkit.dumps(config.doc), encoding="UTF-8")
    click.echo(
        f"The [{CONFIG_TOOL_NITPICK_KEY}] table was updated in {config.file.name!r}:"
        f" {message} appended. {EmojiEnum.STAR_CAKE.value}"
    )
    raise Exit(1)  # A non-zero exit code is needed when executed as a pre-commit hook
