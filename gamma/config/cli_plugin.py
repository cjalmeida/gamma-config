# flake8: noqa
from gamma.cli import plugins
from .cli_command import config
import sys

@plugins.hookimpl
def add_commands():
    return [
        plugins.Command(config),
    ]


plugins.plugin_manager.register(sys.modules[__name__])
