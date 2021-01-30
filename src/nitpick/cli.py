"""Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -mnitpick` python will execute
    ``__main__.py`` as a script. That means there won't be any
    ``nitpick.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there's no ``nitpick.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""
import os
from enum import Enum
from itertools import chain
from pathlib import Path

import click

from nitpick.constants import ERROR_PREFIX, PROJECT_NAME
from nitpick.core import Nitpick


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


@click.command()
@click.option(
    "--project",
    "-p",
    "project_root",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, resolve_path=True),
    help="Path to project root",
)
@click.option(
    f"--{NitpickFlag.OFFLINE.name.lower()}",  # pylint: disable=no-member
    is_flag=True,
    default=False,
    help=NitpickFlag.OFFLINE.value,
)
@click.option(
    "--check",
    "-c",
    is_flag=True,
    default=False,
    help="Don't modify the configuration files, just print the difference."
    " Return code 0 means nothing would change. Return code 1 means some files would be modified.",
)
def nitpick_cli(project_root: Path = None, offline=False, check=False):
    """Enforce the same configuration across multiple projects."""
    if not check:
        click.secho("Apply mode is not yet implemented; running a check instead", fg="red")

    nit = Nitpick.singleton().init(project_root, offline)

    for err in chain(nit.config.merge_styles(), nit.check_present_absent()):
        click.echo(f"{ERROR_PREFIX}{err.number:03} {err.message}{err.suggestion}")
    # FIXME[AA]: follow steps of NitpickExtension.run()
