import click


@click.group()
def config():
    """Configuration related commands"""


@click.command()
def scaffold():
    """Initialize the config folder with samples"""
