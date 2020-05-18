from gamma.cli import plugins


@plugins.hookimpl
def add_commands():
    return [
        plugins.Command(config),
    ]


plugins.plugin_manager.register(sys.modules[__name__])
