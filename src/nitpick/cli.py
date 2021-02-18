"""Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

You might be tempted to import things from __main__ later, but that will cause
problems: the code will get executed twice:

- When you run `python -mnitpick` python will execute ``__main__.py`` as a script.
    That means there won't be any ``nitpick.__main__`` in ``sys.modules``.
- When you import __main__ it will get executed again (as a module) because
    there's no ``nitpick.__main__`` in ``sys.modules``.

Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""
import os
from enum import Enum
from pathlib import Path
from typing import Optional

import click
from click.exceptions import Exit
from loguru import logger

from nitpick.constants import PROJECT_NAME
from nitpick.core import Nitpick
from nitpick.generic import relative_to_current_dir, singleton
from nitpick.violations import ViolationCounter


class _FlagMixin:
    """Private mixin used to test the flags."""

    name: str

    def as_flake8_flag(self) -> str:
        """Format the name of a flag to be used on the CLI."""
        slug = self.name.lower().replace("_", "-")
        return f"--{PROJECT_NAME}-{slug}"

    def as_envvar(self) -> str:
        """Format the name of an environment variable."""
        return f"{PROJECT_NAME.upper()}_{self.name.upper()}"

    def get_environ(self) -> str:
        """Get the value of an environment variable."""
        return os.environ.get(self.as_envvar(), "")


class NitpickFlag(_FlagMixin, Enum):
    """Flags to be used with the CLI."""

    OFFLINE = "Offline mode: no style will be downloaded (no HTTP requests at all)"


@click.group()
@click.option(
    "--project",
    "-p",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, resolve_path=True),
    help="Path to project root",
)
@click.option(
    f"--{NitpickFlag.OFFLINE.name.lower()}",  # pylint: disable=no-member
    is_flag=True,
    default=False,
    help=NitpickFlag.OFFLINE.value,
)
def nitpick_cli(project: Path = None, offline=False):  # pylint: disable=unused-argument
    """Enforce the same configuration across multiple projects."""


def get_nitpick(context: click.Context) -> Nitpick:
    """Create a Nitpick instance from the click context parameters."""
    project = None
    offline = False
    if context.parent:
        project = context.parent.params["project"]
        offline = context.parent.params["offline"]
    project_root: Optional[Path] = Path(project) if project else None
    return Nitpick.singleton().init(project_root, offline)


@nitpick_cli.command()
@click.option(
    "--check",
    "-c",
    is_flag=True,
    default=False,
    help="Don't modify the configuration files, just print the difference."
    " Return code 0 means nothing would change. Return code 1 means some files would be modified.",
)
@click.option("--verbose", "-v", is_flag=True, default=False, help="Verbose logging")
@click.pass_context
@click.argument("files", nargs=-1)
def run(context, check, verbose, files):
    """Apply suggestions to configuration files.

    You can use partial and multiple file names in the FILES argument.
    """
    if verbose:
        logger.enable(PROJECT_NAME)

    nit = get_nitpick(context)
    for fuss in nit.run(*files, check=check):
        nit.echo(fuss.pretty)

    counter: ViolationCounter = singleton(ViolationCounter)
    if counter.manual or counter.fixed:
        click.secho(counter.summary)
        raise Exit(1)


@nitpick_cli.command()
@click.pass_context
@click.argument("files", nargs=-1)
def ls(context, files):  # pylint: disable=invalid-name
    """List of files configured in the Nitpick style.

    Display existing files in green and absent files in red.
    You can use partial and multiple file names in the FILES argument.
    """
    nit = get_nitpick(context)
    violations = list(nit.project.merge_styles(nit.offline))
    if violations:
        for fuss in violations:
            click.echo(fuss.pretty)
        raise Exit(1)  # TODO: test ls with invalid style

    # TODO: test API .configured_files
    for file in nit.configured_files(*files):
        click.secho(relative_to_current_dir(file), fg="green" if file.exists() else "red")
