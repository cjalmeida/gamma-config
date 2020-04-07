import sys
from typing import Any, Callable, Dict, Iterable

import pluggy

try:
    from dataclasses import dataclass
except ModuleNotFoundError:
    # shim for 3.6
    from attr import dataclass


PROJECT_NAME = "gamma-config"
hookspec = pluggy.HookspecMarker(PROJECT_NAME)
hookimpl = pluggy.HookimplMarker(PROJECT_NAME)


@dataclass
class TagSpec:
    """Data class declaring tags"""

    # Tag name. Must start with "!" per YAML spec
    tag: str

    # The function to handle the YAML tag. See
    # ```gamma.config.tags.tag_handler_spec``` for the available parameters
    handler: Callable


@hookspec
def add_tags() -> Iterable[TagSpec]:
    """Register tags to gamma-config"""


@hookspec
def expr_globals() -> Dict[str, Any]:
    """Add global values when evaluating !expr nodes"""


class TagException(Exception):
    pass


# create a manager and add the spec
plugin_manager = pluggy.PluginManager(PROJECT_NAME)
plugin_manager.add_hookspecs(sys.modules[__name__])
