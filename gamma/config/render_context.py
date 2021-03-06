from gamma import dispatch
from typing import Dict, List, Optional, NamedTuple, Callable, Any
from .cache import cache


class ContextVar(NamedTuple):
    """A specification for a context variable used for rendering dynamic values.

    Either if ``function`` is specified, we'll call the function to get the actual
    value.
    """

    # The name of the variable
    name: str

    # The value of the variable
    value: Any = None

    # function to call to resolve the variable
    function: Optional[Callable[..., Any]] = None

    # If True, will cache the function result, otherwise will call on each render
    cacheable: bool = False


def default_context_provider():
    """Add to the render context some defaults.

    - env -> os.environ
    - c -> the global RootConfig
    """
    import os
    from .globalconfig import get_config

    return [ContextVar("env", os.environ), ContextVar("c", function=get_config)]


# Provides a list of context providers. You can add your own if needed
context_providers: List[Callable] = [default_context_provider]


def get_render_context() -> Dict[str, Any]:
    """Return the render context by calling each function in ``context_provider``.

    The function signature must be one of:
        () -> List[ContextVar]

    """
    out = {}
    for provider in context_providers:
        var: ContextVar
        for var in provider():
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
