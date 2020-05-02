import os
import sys
from typing import Any

from gamma.config.config import Config

from . import plugins


def env(value: Any) -> str:
    """Maps the value to an environment variable of the same name.

    You can provide a default using the ``|`` (pipe) character after the variable
    name.

    Examples:

        my_var: !env MYVAR|my_default
    """

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
    """Similar to !env, but never returns the value when dumping."""

    if dump:
        return node
    return env(value)


def expr(value: Any) -> Any:
    """Uses ``eval()`` to render arbitrary Python expressions.

    See ``expr_globals`` plugin hook to extend available globals.
    """

    _locals = {}
    _globals = {}

    for var in plugins.plugin_manager.hook.expr_globals():
        for k, v in var.items():
            if k in _globals:
                raise Exception(f"Global key `{k}` defined twice in plugins.")
            _globals[k] = v

    return eval(value, _globals, _locals)


def ref(value: Any, root: Config) -> Any:
    """References other entries in the config object.

    Navigate the object using the dot notation. Complex named keys can be accessed
    using quotes.
    """

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
def cli(value: str):
    """Return a command line option argument.

    You can specify options using the :func:``gamma.config.cli.option`` decorator. They
    can be referenced then using the `!cli <option_long_name>`.

    Examples:

        Given a command::

        @click.command()
        @option('-a', '--myarg')
        def foo(myarg):
            ...

        You can reference the value of `--myarg` as::

        args:
            myarg: !cli myarg

    See:
        :func:``gamma.config.cli.option``
    """

    from gamma.config.cli import get_option

    opt_value = get_option(value)
    return opt_value


@plugins.hookimpl
def add_tags():
    """Add builtin tags to the YAML parsers"""

    return [
        plugins.TagSpec("!env", env),
        plugins.TagSpec("!env_secret", env_secret),
        plugins.TagSpec("!expr", expr),
        plugins.TagSpec("!ref", ref),
        plugins.TagSpec("!cli", cli),
    ]


@plugins.hookimpl
def expr_globals():
    """Add the ``os.environ`` dict to !expr globals.

    Mostly an example.
    """

    return {"env": os.environ}


plugins.plugin_manager.register(sys.modules[__name__])
