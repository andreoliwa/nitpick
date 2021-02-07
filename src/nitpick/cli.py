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
from nitpick.generic import relative_to_cur_home_abs


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
def run(context, check=False, verbose=False):
    """Apply suggestions to configuration files."""
    if verbose:
        logger.enable(PROJECT_NAME)

    if not check:
        logger.warning("Apply mode is not yet implemented; running a check instead")

    nit = get_nitpick(context)
    violations = 0
    for fuss in nit.run():
        violations += 1
        nit.echo(fuss.pretty)

    if violations:
        plural = "s" if violations > 1 else ""
        click.secho(f"❌ {violations} violation{plural}.")
        raise Exit(1)


@nitpick_cli.command()
@click.pass_context
def ls(context):  # pylint: disable=invalid-name
    """List of files configured in the Nitpick style."""
    nit = get_nitpick(context)
    fusses = list(nit.project.merge_styles(nit.offline))
    if fusses:
        for fuss in fusses:
            click.echo(fuss.pretty)
        raise Exit(1)  # FIXME[AA]: test ls with invalid style

    # FIXME[AA]: test API .configured_files
    for file in nit.configured_files:  # type: Path
        click.echo(relative_to_cur_home_abs(file) + " ", nl=False)
        if file.exists():
            click.secho("(exists)", fg="green")
        else:
            click.secho("(not found)", fg="red")
