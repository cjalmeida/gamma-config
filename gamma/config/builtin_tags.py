import os
import sys
import threading
from typing import Any, Dict

from gamma.config.config import Config, RenderContext

from . import plugins

UNDEFINED = "~~UNDEFINED~~"


def _split_default(value):
    """Get a value optional default, using the content after the last "|"
    (pipe) as convention"""

    default = UNDEFINED
    parsed = value
    if "|" in value:
        parsed, default = value.rsplit("|", 1)
    return parsed, default


def env(value: Any) -> str:
    """Maps the value to an environment variable of the same name.

    You can provide a default using the ``|`` (pipe) character after the variable
    name.

    Examples:

        my_var: !env MYVAR|my_default
    """
    name = value
    name, default = _split_default(name)
    env_val = os.getenv(name, default)
    if env_val == UNDEFINED:
        raise plugins.TagException(
            f"Env variable '{name}' not found when resolving node and no default set"
        )

    return env_val


def dump_raw(dump: bool, node) -> str:
    if dump:
        return RenderContext(node, render_recurse=False)
    return node


def env_secret(value: Any, dump: bool, node) -> str:
    """Similar to !env, but never returns the value when dumping."""
    if dump:
        return node
    return env(value)


def expr(value: Any, root) -> Any:
    """Uses ``eval()`` to render arbitrary Python expressions.

    By default, we add the root configuration as `c` variable.

    See ``expr_globals`` plugin hook to extend available globals.
    """

    _locals = {"c": root}
    _globals = {}

    for var in plugins.plugin_manager.hook.expr_globals():
        for k, v in var.items():
            if k in _globals:
                raise Exception(f"Global key `{k}` defined twice in plugins.")
            _globals[k] = v

    return eval(value, _globals, _locals)


j2_cache = threading.local()


def j2(value: Any, root) -> Any:
    """Treats the value a Jinj2 Template

    The context for rendering is shared with the ``!expr`` and can be extended with
    the same ``expr_globals`` plugin hook.

    In practice, in the snippet bellow, ``foo1`` and ``foo2`` are equivalent

        myvar: 100
        foo1: !expr f"This is a number = {c.myvar}"
        foo2: !j2 This is a number = {c.myvar}

    Notes:
        * Jinja2 is not installed by default, you should install it manually.
    """
    try:
        import jinja2
    except ModuleNotFoundError:
        raise Exception(
            "Could not find Jinja2 installed. You must manually install it with "
            "`pip install jinja2` if you want to use the !j2 tag"
        )

    _globals = {"c": root}

    for var in plugins.plugin_manager.hook.expr_globals():
        for k, v in var.items():
            if k in _globals:
                raise Exception(f"Global key `{k}` defined twice in plugins.")
            _globals[k] = v

    if not hasattr(j2_cache, "env"):
        j2_cache.env = jinja2.Environment()

    res = j2_cache.env.from_string(value).render(**_globals)
    return res


def func(node: Any, dump):
    """Returns a reference to a function.

    Functions are provided as a mapping in the structure below:

        my_function: !func
            call: <module>:<func_name>  # reference to the callable
            args: [<arg1>, <arg2>]      # (optional) positional args
            kwargs:                     # (optional) keyword args
                <param1>: <value1>
                <param2>: <value2>
            dump: <dump>                # (optional) dump mode behavior

    The function is resolved and a ``partial`` is returned. The ``dump`` arg defaults
    to ``false`` and means the function is not resolved during serialization. If
    ``true``, the function is called and it's content resolved - as expected this
    won't work for partials that require extra configuration.
    """

    import importlib
    from functools import partial

    assert isinstance(node, Dict), "Value should be a mapping"

    param_keys = set(node.keys())
    expected_keys = set(["call", "args", "kwargs", "dump"])
    extra = param_keys - expected_keys
    assert not extra, f"Extra keys found in !func configuration: {extra}"

    try:
        module_name, func_name = node["call"].split(":")
    except ValueError as ex:
        raise ValueError(
            "Error parsing callable: '" + node["call"] + "'. Expecting <module>:<func>"
        ) from ex
    module = importlib.import_module(module_name)
    _func = getattr(module, func_name)

    args = node.get("args", [])
    kwargs = node.get("kwargs", {})
    curried = partial(_func, *args, **kwargs)

    to_dump = node.get("dump", False)
    if dump and to_dump:
        return curried()
    elif dump and not to_dump:
        return node
    else:
        return curried


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
def option(value: str):
    """Return a command line option argument.

    You can specify options using the :func:``gamma.config.cli.option`` decorator. They
    can be referenced then using the `!option <option_long_name>|<default>`.

    Examples:

        Given a command::

        @click.command()
        @option('-a', '--myarg')
        def foo(myarg):
            ...

        You can reference the value of `--myarg` as::

        args:
            myarg: !option myarg

    See:
        :func:``gamma.config.cli.option``
    """

    from gamma.config.cli import get_option

    value, default = _split_default(value)
    try:
        opt_value = get_option(value)
    except KeyError:
        opt_value = default

    if opt_value == UNDEFINED:
        raise plugins.TagException(
            f"CLI param '{value}' not set and no default provided."
        )
    return opt_value


@plugins.hookimpl
def add_tags():
    """Add builtin tags to the YAML parsers"""

    return [
        plugins.TagSpec("!env", env),
        plugins.TagSpec("!env_secret", env_secret),
        plugins.TagSpec("!dump_raw", dump_raw),
        plugins.TagSpec("!expr", expr),
        plugins.TagSpec("!func", func),
        plugins.TagSpec("!j2", j2),
        plugins.TagSpec("!ref", ref),
        plugins.TagSpec("!option", option),
    ]


@plugins.hookimpl
def expr_globals():
    """Add the ``os.environ`` dict to !expr globals.

    Mostly an example.
    """

    return {"env": os.environ}


plugins.plugin_manager.register(sys.modules[__name__])
