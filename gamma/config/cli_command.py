import sys
import os
import click
import shutil

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

    from pathlib import Path
    import gamma.config as root_mod

    if not target:
        target = Path(".").absolute()

    print(f"TARGET: {target}")
    target = Path(target)
    confdir: Path = target / "config"
    meta: Path = confdir / "00-meta.yaml"

    # find source in either the local folder or under the sys.prefix
    src = Path(root_mod.__file__).parents[2] / "config"
    if not src.exists():
        src = Path(sys.prefix) / "etc/gamma-config/config"

    if not src.exists():
        raise Exception(
            f"Could not find template config in either ./config or under {src}"
        )

    # Check if config/00-meta.yaml already exists
    if not force and meta.exists():
        click.secho(
            "ERROR: File 'config/00-meta.yaml' already exists "
            "and --force was not set",
            fg="yellow",
        )
        raise SystemExit(1)

    confdir.mkdir(exist_ok=True)
    _recursive_copy(src, confdir)
    click.secho("Copied config samples to: ", fg="yellow", nl=False)
    click.secho(str(confdir), fg="cyan")


def _recursive_copy(src, dest):
    """
    Copy each file from src dir to dest dir, including sub-directories.
    """
    for item in os.listdir(src):
        file_path = os.path.join(src, item)

        # if item is a file, copy it
        if os.path.isfile(file_path):
            shutil.copy(file_path, dest)

        # else if item is a folder, recurse
        elif os.path.isdir(file_path):
            new_dest = os.path.join(dest, item)
            os.mkdir(new_dest)
            _recursive_copy(file_path, new_dest)
