from typing import Any, Callable, Dict, List, NamedTuple, Optional, Union

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


def default_context_provider():
    """Render context some defaults.

    - `env` -> os.environ
    - `c` -> the global RootConfig
    """
    import os
    from .globalconfig import get_config

    return [ContextVar("env", os.environ), ContextVar("c", function=get_config)]


context_providers: List[Union[Callable, List[ContextVar]]] = [default_context_provider]
"""Provides a list of context providers. You can add your own if needed by appending
a function with the signature `() -> List[ContextVar]` or adding a list of
`ContextVar` objects
"""


def get_render_context() -> Dict[str, Any]:
    """Return the render context by calling each function in ``context_provider``.

    A context provider must be a function with the signature:
        () -> List[ContextVar]
    or simply a list of [ContextVar] objects

    """
    out = {}
    for provider in context_providers:
        var: ContextVar
        vars: List[ContextVar] = provider() if callable(provider) else provider
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
