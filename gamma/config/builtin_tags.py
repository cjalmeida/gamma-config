import os
import sys
from typing import Any

from gamma.config.config import Config

from . import plugins


def env(value: Any) -> str:

    NO_DEFAULT = "~~NO-DEFAULT~~"

    default = NO_DEFAULT
    name = value
    if "|" in name:
        name, default = name.split("|")

    value = os.getenv(name, default)
    if value == NO_DEFAULT:
        raise plugins.TagException(
            f"Env variable '{name}' not found when resolving node and no default set"
        )

    return value


def env_secret(value: Any, dump: bool, node) -> str:
    if dump:
        return node
    return env(value)


def expr(value: Any) -> Any:
    _locals = {}
    _globals = {}

    for var in plugins.plugin_manager.hook.expr_globals():
        for k, v in var.items():
            if k in _globals:
                raise Exception(f"Global key `{k}` defined twice in plugins.")
            _globals[k] = v

    return eval(value, _globals, _locals)


def code(value: Any) -> Any:
    _locals = {}
    _global = {}
    exec(value, _global, _locals)
    if "out" not in _locals:
        raise Exception("!code tag must assign the output to an 'out' variable")
    return _locals["out"]


def ref(value: Any, root: Config) -> Any:
    import shlex
    import operator
    import functools

    lex = shlex.shlex(instream=value, posix=True)
    lex.whitespace = "."
    tokens = []
    token = lex.get_token()
    while token:
        tokens.append(token)
        token = lex.get_token()

    return functools.reduce(operator.getitem, tokens, root)


@plugins.hookimpl
def add_tags():
    return [
        plugins.TagSpec("!env", env),
        plugins.TagSpec("!env_secret", env_secret),
        plugins.TagSpec("!expr", expr),
        plugins.TagSpec("!code", code),
        plugins.TagSpec("!ref", ref),
    ]


@plugins.hookimpl
def expr_globals():
    return {"env": os.environ}


plugins.plugin_manager.register(sys.modules[__name__])
