"""Module handling rendering context variables (eg. for !expr and !j2)"""
from functools import partial
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Union

from gamma.config.confignode import ConfigNode

from .cache import cache


class ContextVar(NamedTuple):
    """A specification for a context variable used for rendering dynamic values.

    Either if ``function`` is specified, we'll call the function to get the actual
    value.
    """

    name: str
    """The name of the variable"""

    value: Any = None
    """The value of the variable"""

    function: Optional[Callable[..., Any]] = None
    """Function to call to resolve the variable"""

    cacheable: bool = False
    """If True, will cache the function result, otherwise will call on each render."""


def get_render_context(**kwargs) -> Dict[str, Any]:
    """Return the render context by calling each function in ``context_provider``.

    A context provider must be a function with the signature:
        `(**kwargs) -> List[ContextVar]`
    or simply a list of `ContextVar` objects

    The provided `**kwargs` are the same available in the `render_node` function
    """
    out = {}
    for provider in context_providers:
        var: ContextVar
        vars: List[ContextVar] = provider(**kwargs) if callable(provider) else provider
        for var in vars:
            if var.cacheable:
                cache_key = f"render_context/{var.name}"
                try:
                    out[var.name] = cache[cache_key]
                    continue
                except KeyError:
                    pass

            if var.function is not None:
                val = var.function()
            else:
                val = var.value

            if var.cacheable:
                cache[cache_key] = val

            out[var.name] = val

    return out


###
# Built-in providers
###


def base_provider(**kwargs):
    """Defaults to context

    - `env` -> os.environ
    - `c` -> the global RootConfig
    """
    import os
    from .globalconfig import get_config

    return [
        ContextVar("env", os.environ),
        ContextVar("c", function=partial(get_config, False)),
    ]


def underscore_context_provider(*, config: ConfigNode = None, **kwargs):
    """Look in parent config nodes and add all entries under the `_context` key"""

    vars = []
    if not config:
        return vars

    while config._parent is not None:
        config = config._parent
        ctx: dict = config.get("_context", {})
        for key, value in ctx.items():
            vars.append(ContextVar(key, value))

    return vars


context_providers: List[Union[Callable, List[ContextVar]]] = [
    base_provider,
    underscore_context_provider,
]
"""Provides a list of context providers. See :func:get_render_context() for details
"""
