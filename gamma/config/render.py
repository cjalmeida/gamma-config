"""Base render_node methods"""

import logging
from typing import Any, Optional

from gamma.config.confignode import ConfigNode, RootConfig  # noqa
from gamma.dispatch import dispatch
from ruamel.yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

from . import tags
from .rawnodes import get_entries, get_values

logger = logging.getLogger(__name__)


class RenderDispatchError(Exception):
    pass


@dispatch
def render_node(
    node: Node,
    tag: tags.Tag,
    *,
    key: Optional[Node] = None,
    config: "ConfigNode" = None,
    dump: bool = False,
    recursive: bool = False,
    path: Optional[str] = None,
):
    """Spec for tag handling functions.

    This function is dispatched first on the specific (Node, Tag) types. If the tag
    name contains a `:` (colon) character, the tag name is interpreted as a URI and
    we fallback to dispatching by the "scheme" portion of the URI and add an extra
    `path` kwarg to the method call. Example:

    ```
    foo: !mytag 1
    ```

    Will be dispatched solely on (ScalarNode, Tag["!mytag"]) types. Whereas

    ```
    foo: !mytag:bar 1
    ```

    Will first be dispatched on (ScalarNode, Tag["!mytag:bar"]), then on
    (ScalarNode, Tag["!mytag"]), the last one with the optional `path` kwargs filled
    as `bar`

    Args:
        node: The raw ruamel YAML node. Can be returned during a dump to keep
            the field dynamic or hide sensitive values.
        tag: The tag to be handled. A subinstance of ``Tag``.
    Keywork Args:
        key: The node key, also as a ruamel YAML node.
        config: The current ConfigNode object.
        dump: Flag indicating we're dumping the data to a potentially insecure
            destination, so sensitive data should not be returned.
        recursive: If true, tag handlers should recursively render nodes.
        path: The URI path for URI fallback dispatch

    Return:
        any value
    """

    if ":" in tag.name:
        # try scheme based dispatch
        scheme, path = tag.name.split(":", 1)
        SchemeTag = tags.Tag[scheme]
        return render_node(
            node, SchemeTag(), key=key, config=config, dump=dump, path=path
        )

    # not found errror
    msg = f"""Renderer not implemented for node_type={type(node).__name__}, tag={tag.name}
    Possible causes:
        * Check if you forgot to import `gamma.config.render_node` when defining your
          `def render_node` method.
    """  # noqa
    raise RenderDispatchError(msg)


@dispatch
def render_node(node: Node, **args) -> Any:
    """Render node.

    Construct a parameterized `Tag` class from `node.tag` and call
    `render_node(Node, Tag)`
    """

    TagClass = tags.Tag[node.tag]
    return render_node(node, TagClass(), **args)


@dispatch
def render_node(node: ScalarNode, tag: tags.Str, **args):
    """Render scalar string"""
    return node.value


@dispatch
def render_node(node: ScalarNode, tag: tags.Int, **args):
    """Render scalar int"""
    return int(node.value)


@dispatch
def render_node(node: ScalarNode, tag: tags.Float, **args):
    """Render scalar float"""
    return float(node.value)


@dispatch
def render_node(node: ScalarNode, tag: tags.Null, **args):
    """Render scalar null"""
    return None


@dispatch
def render_node(node: ScalarNode, tag: tags.Bool, **args):
    """Render scalar boolean. Accepts YAML extended interpretation of `bool`s, like
    `ruamel.yaml`
    """

    val = node.value.lower()
    if val in ("y", "yes", "true", "on", "1"):
        return True
    elif val in ("n", "no", "false", "off", "0"):
        return False
    else:
        raise ValueError(f"Can't convert '{node.value}' to bool")


@dispatch
def render_node(node: ScalarNode, tag: tags.Timestamp, **args):
    """Render timestamp node as `datetime.datetime`. Use `dateutil.parser` module"""
    from dateutil import parser

    return parser.parse(node.value)


@dispatch
def render_node(node: SequenceNode, tag: tags.Seq, **args):
    """Render `seq` nodes recursively"""
    subargs = args.copy()

    out = []
    for subvaluenode in get_values(node):
        subvalue = render_node(subvaluenode, **subargs)
        out.append(subvalue)

    return out


@dispatch
def render_node(node: MappingNode, tag: tags.Map, **args):
    """Render `map` nodes recursively"""
    subargs = args.copy()

    out = {}
    for subkeynode, subvaluenode in get_entries(node):
        subkey = render_node(subkeynode, **args)
        subargs["key"] = subkeynode
        subvalue = render_node(subvaluenode, **subargs)
        out[subkey] = subvalue

    return out


@dispatch
def render_node(cfg: "RootConfig", **args):
    """Render the resulting node of merging all entries"""

    from gamma.config.merge import merge_nodes

    nodes = list(cfg._root_nodes.values())
    _, node = merge_nodes(nodes)
    args.setdefault("config", cfg)
    args.setdefault("dump", False)
    return render_node(node, **args)


@dispatch
def render_node(cfg: "ConfigNode", **args):
    """Render the config node.

    Args:
        dump: If true, assume it's "dump mode" where secrets are not to be rendered.
    """
    args.setdefault("config", cfg)
    args.setdefault("dump", False)
    return render_node(cfg._node, **args)


from . import builtin_tags  # noqa isort:skip
