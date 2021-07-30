"""Module that implements renderers for builtin-tags"""

import importlib
import os
import threading
from typing import Any, Union

from gamma.config.confignode import ConfigNode
from gamma.config.dump_dict import to_dict
from gamma.dispatch import dispatch
from jinja2.runtime import StrictUndefined
from ruamel.yaml import YAML
from ruamel.yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

from .findconfig import get_config_root
from .render import render_node
from .render_context import get_render_context
from .tags import Tag, TagException

UNDEFINED = "~~UNDEFINED~~"
yaml = YAML(typ="safe")


RefTag = Tag["!ref"]
EnvTag = Tag["!env"]
EnvSecretTag = Tag["!env_secret"]
ExprTag = Tag["!expr"]
J2Tag = Tag["!j2"]
J2SecretTag = Tag["!j2_secret"]
PyTag = Tag["!py"]
ObjTag = Tag["!obj"]
PathTag = Tag["!path"]

j2_cache = threading.local()


@dispatch
def render_node(node: Node, tag: EnvTag, **ctx) -> str:
    """[!env] Maps the value to an environment variable of the same name.

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
def render_node(node: Node, tag: EnvSecretTag, *, dump=False, **ctx) -> str:
    """[!env_secret] Similar to !env, but never returns the value when dumping."""
    if dump:
        return node
    return render_node(node, EnvTag(), dump=dump, **ctx)


# process: !expr
@dispatch
def render_node(node: Node, tag: ExprTag, **ctx) -> Any:
    """[!expr] Uses ``eval()`` to render arbitrary Python expressions.

    By default, we add the root configuration as `c` variable.

    See ``gamma.config.render_context.context_providers`` documentation to add your
    own variables to the context.
    """

    _locals = {}
    _globals = get_render_context(node=node, tag=tag, **ctx)
    return eval(node.value, _globals, _locals)


@dispatch
def render_node(node: Node, tag: J2Tag, *, config=None, key=None, **ctx) -> Any:
    """[!j2] Treats the value a Jinj2 Template

    See ``gamma.config.render_context.context_providers`` documentation to add your
    own variables to the context.

    In practice, in the snippet bellow, ``foo1`` and ``foo2`` are equivalent

        myvar: 100
        foo1: !expr f"This is a number = {c.myvar}"
        foo2: !j2 This is a number = {c.myvar}

    You can customize the Jinja2 environment by providing a reference to a Python
    function in the `j2_env` key in `00-meta.yaml`. Example

        j2_env: my_app.my_module:my_func

    Notes:
        * Jinja2 is not installed by default, you should install it manually.
    """
    try:
        import jinja2
        import jinja2.exceptions
    except ModuleNotFoundError:  # pragma: no cover
        raise Exception(
            "Could not find Jinja2 installed. You must manually install it with "
            "`pip install jinja2` if you want to use the !j2 tag"
        )

    render_ctx = get_render_context(node=node, tag=tag, config=config, key=key, **ctx)

    if not hasattr(j2_cache, "env"):
        root = config and config._root
        env_factory = root.get("j2_env")
        if env_factory:
            module_name, func_name = env_factory.split(":", 1)
            mod = importlib.import_module(module_name)
            func = getattr(mod, func_name)
            j2_cache.env = func()
        else:
            j2_cache.env = jinja2.Environment(undefined=StrictUndefined)

    try:
        res = j2_cache.env.from_string(node.value).render(**render_ctx)
    except jinja2.exceptions.UndefinedError as ex:
        msg = f'Error rendering key `{key.value}: "{node.value}"` -> {ex.message}'
        raise ValueError(msg)

    return res


# process: !j2_secret
@dispatch
def render_node(node: Node, tag: J2SecretTag, *, dump=False, **ctx) -> Any:
    """[!j2_secret] Similar to !j2, but never returns the value when dumping."""

    if dump:
        return node
    return render_node(node, J2Tag(), dump=dump, **ctx)


@dispatch
def render_node(node: Node, tag: RefTag, *, config=None, recursive=False, **ctx) -> Any:
    """[!ref] References other entries in the config object.

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

    parent = functools.reduce(operator.getitem, tokens[:-1], config._root)
    val = parent[tokens[-1]]

    if recursive:
        while isinstance(val, (ConfigNode, Node)):
            # chain dump if needed
            val = render_node(val, config=config, recursive=recursive, **ctx)

    return val


# process: !py
@dispatch
def render_node(node: ScalarNode, tag: PyTag, *, path=None, **ctx) -> Any:
    """[!py] Pass the node value to a Python callable.

    This tag should be used as a URI-style tag on the form `!py:<module>:<callable>`

    The scalar node value is first implicitly resolved to a Python object using
    `yaml.load`. For instance:

    ```yaml
    foo: !py:myapp.mymodule:myfunc 100
    bar: !py:myapp.mymodule:myfunc "100"
    zig: !py:myapp.mymodule:myfunc a value
    ```

    Will call the function `myfunc` in `myapp.mymodule` module with the arguments:
    - `type(value) == int; value == 100` for `foo`
    - `type(value) == str; value == "100"` for `bar`
    - `type(value) == str; value == "a value"` for `zig`
    """

    func = _py_tag_get_func("py", path)
    val = yaml.load(node.value)
    return func(val)


# process: !py
@dispatch
def render_node(
    node: Union[SequenceNode, MappingNode], tag: PyTag, *, path=None, **ctx
) -> Any:
    """[!py] Pass the node value to a Python callable.

    This tag should be used as a URI-style tag on the form `!py:<module>:<callable>`

    The `map` or `seq` node value is first converted to a Python `dict`/`list`
    recursively using the `to_dict` method.
    """

    func = _py_tag_get_func("py", path)
    val = to_dict(node, **ctx)
    return func(val)


def _py_tag_get_func(tag, path, default_module=None):
    """Get the callable for a given tag `path` argument

    Used by `!py`, `!obj` tags meta config.

    Args:
        tag: either "obj" or "py"
        path: the tag "path" part in the format `!<tag>:<module>:<callable>`
    """

    import importlib

    if not path:
        raise ValueError(f"The !{tag} tag is missing the 'path' part after the ':'")

    if ":" in path:
        module_name, func_name = path.split(":", 1)
    elif tag == "obj" and default_module:
        module_name = default_module
        func_name = path
    else:
        raise ValueError(f"The !{tag} tag has an invalid reference: {path}")

    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as ex:
        raise ValueError(f"Module part from '!{tag}:{path}' not found") from ex

    func = getattr(module, func_name, None)
    if not func:
        raise ValueError(f"Name '{func_name}' not found in module {module}")

    return func


# process: !obj
@dispatch
def render_node(
    node: MappingNode, tag: ObjTag, *, path=None, config=None, **ctx
) -> Any:
    """[!obj] Create a Python object by passing the mapping value as nested dicts to
    the object constructor.

    This tag should be used as a URI-style tag on the form `!obj:<module>:<callable>`
    It behaves like `!py`, but only applies to `map` nodes, and
    automatically unpack the mapping.

    You may omit the `<module>` part of the path if you define an `obj_default_module`
    scalar entry at the root of the config.

    Examples:

    ```yaml
    foo: !obj:myapp.mymodule:MyClass
        a: 100
        b: a value

    # the above `foo` is equivalent to `bar` below

    obj_default_module: myapp.mymodule

    bar: !obj:MyClass
        a: 100
        b: a value
    ```
    """

    root = config and config._root
    default_module = (root and root.get("obj_default_module")) or None
    func = _py_tag_get_func("obj", path, default_module=default_module)
    val = to_dict(node)
    return func(**val)


# process: !path
@dispatch
def render_node(node: Node, tag: PathTag, **ctx) -> str:
    """[!path] Construct an absolute file path by joining a path
    fragment to the known path of the *parent* of config root directory

    Examples:
        # should point to `<config-root>/../data/hello_world.csv`
        my_var: !path data/hello_world.csv
    """
    path_fragment = node.value
    base = get_config_root().parent
    return str(base.joinpath(path_fragment).absolute())


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
