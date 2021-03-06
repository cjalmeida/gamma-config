import os
import pdb
import threading
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.nodes import Node
from .tags import Tag, TagException
from gamma.dispatch import dispatch
from .render import render_node
from .render_context import get_render_context

UNDEFINED = "~~UNDEFINED~~"
yaml = YAML(typ="safe")


RefTag = Tag["!ref"]
EnvTag = Tag["!env"]
EnvSecretTag = Tag["!env_secret"]
ExprTag = Tag["!expr"]
J2Tag = Tag["!j2"]
J2SecretTag = Tag["!j2_secret"]



j2_cache = threading.local()


# render !env
@dispatch
def render_node(node: Node, tag: EnvTag, **ctx) -> str:
    """Maps the value to an environment variable of the same name.

    You can provide a default using the ``|`` (pipe) character after the variable
    name.

    Examples:

        my_var: !env MYVAR|my_default
    """
    name = node.value
    name, default = _split_default(name)
    env_val = os.getenv(name, default)
    if env_val == UNDEFINED:
        raise TagException(
            f"Env variable '{name}' not found when resolving node and no default set"
        )

    return env_val


# process: !env_secret
@dispatch
def render_node(node: Node, tag: EnvSecretTag, dump=False, **ctx) -> str:
    """Similar to !env, but never returns the value when dumping."""
    if dump:
        return node
    return render_node(node, EnvTag(), dump=dump, **ctx)


# process: !expr
@dispatch
def render_node(node: Node, tag: ExprTag, **ctx) -> Any:
    """Uses ``eval()`` to render arbitrary Python expressions.

    By default, we add the root configuration as `c` variable.

    See ``gamma.config.render_context.context_providers`` documentation to add your
    own variables to the context.
    """

    _locals = {}
    _globals = get_render_context()
    return eval(node.value, _globals, _locals)


# process: !expr
@dispatch
def render_node(node: Node, tag: J2Tag, **ctx) -> Any:
    """Treats the value a Jinj2 Template

    See ``gamma.config.render_context.context_providers`` documentation to add your
    own variables to the context.

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

    render_ctx = get_render_context()
    if not hasattr(j2_cache, "env"):
        j2_cache.env = jinja2.Environment()

    res = j2_cache.env.from_string(node.value).render(**render_ctx)
    return res


# process: !j2_secret
@dispatch
def render_node(node: Node, tag: J2SecretTag, dump=False, **ctx) -> Any:
    """Similar to !j2, but never returns the value when dumping."""

    if dump:
        return node
    return render_node(node, J2Tag(), dump=dump, **ctx)


# process: !ref
@dispatch
def render_node(node: Node, tag: RefTag, config=None, **ctx) -> Any:
    """References other entries in the config object.

    Navigate the object using the dot notation. Complex named keys can be accessed
    using quotes.
    """

    import functools
    import operator
    import shlex

    lex = shlex.shlex(instream=node.value, posix=True)
    lex.whitespace = "."
    tokens = []
    token = lex.get_token()
    while token:
        tokens.append(token)
        token = lex.get_token()

    # old_mode = root.dump_mode
    try:
        # root.dump_mode = False
        parent = functools.reduce(operator.getitem, tokens[:-1], config._root)
    finally:
        1
        # root.dump_mode = old_mode

    return parent[tokens[-1]]


###
# Utilities
###


def _split_default(value):
    """Get a value optional default, using the content after the last "|"
    (pipe) as convention.

    The default will be parsed as a YAML value.
    """

    default = UNDEFINED
    parsed = value
    if "|" in value:
        parsed, default = value.rsplit("|", 1)
        default = yaml.load(default)
    return parsed, default
