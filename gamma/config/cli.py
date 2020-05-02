import sys

import click
from gamma.cli import plugins


@click.group()
def config():
    """Application configuration related commands"""


@config.command()
@click.option("-t", "--target", help="The target folder. Default to current folder.")
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="If set, do not check for existing files.",
)
def scaffold(target, force):
    """Initialize the config folder with samples"""

    import shutil
    import os
    from pathlib import Path
    import gamma.config as root_mod

    if not target:
        target = os.path.abspath(root_mod.get_project_home())

    target = Path(target)
    confdir: Path = target / "config"
    meta: Path = confdir / "00-meta.yaml"

    # find source in either the local folder or under the sys.prefix
    src = Path(root_mod.__file__).parents[2] / "config"
    if not src.exists():
        src = Path(sys.prefix) / "etc/gamma-config/config"

    if not src.exists():
        raise Exception(
            "Could not find template config in either ./config or under {src}"
        )

    # Check if config/00-meta.yaml already exists
    if not force and meta.exists():
        click.secho(
            "ERROR: File 'config/00-meta.yaml' already exists "
            "and --force was not set",
            fg="yellow",
        )
        raise SystemExit(1)

    shutil.copytree(src, confdir)
    click.secho("Copied config samples to: ", fg="yellow", nl=False)
    click.secho(str(confdir), fg="cyan")


@plugins.hookimpl
def add_commands():
    return [
        plugins.Command(config),
    ]


plugins.plugin_manager.register(sys.modules[__name__])
