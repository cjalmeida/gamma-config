import logging
from typing import Optional
from ruamel.yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

from gamma.dispatch import dispatch

from . import tags
from .rawnodes import get_items, get_values

logger = logging.getLogger(__name__)


@dispatch
def render_node(
    node: Node,
    tag: tags.Tag,
    *,
    key: Optional[Node] = None,
    config: "ConfigNode" = None,
    dump: bool = False,
):
    """Spec for tag handling functions.

    Functions may accept any argument (or none at all), as needed.

    Args:
        node: The raw ruamel YAML node. Can be returned during a dump to keep
            the field dynamic or hide sensitive values.
        tag: The tag to be handled. A subinstance of ``Tag``.
    Keywork Args:
        key: The node key, also as a ruamel YAML node.
        config: The current ConfigNode object.
        dump: Flag indicating we're dumping the data to a potentially insecure
            destination, so sensitive data should not be returned.

    Return:
        any value
    """
    raise ValueError(
        f"Renderer not implemented for node_type={type(node).__name__}, tag={tag.name}"
    )


@dispatch
def render_node(node: ScalarNode, tag: tags.Str, **args):
    return node.value


@dispatch
def render_node(node: ScalarNode, tag: tags.Int, **args):
    return int(node.value)


@dispatch
def render_node(node: ScalarNode, tag: tags.Float, **args):
    return float(node.value)


@dispatch
def render_node(node: ScalarNode, tag: tags.Null, **args):
    return None


@dispatch
def render_node(node: ScalarNode, tag: tags.Bool, **args):
    val = node.value.lower()
    if val in ("y", "yes", "true", "on", "1"):
        return True
    elif val in ("n", "no", "false", "off", "0"):
        return False
    else:
        raise ValueError(f"Can't convert '{node.value}' to bool")


@dispatch
def render_node(node: ScalarNode, tag: tags.Timestamp, **args):
    from dateutil import parser

    return parser.parse(node.value)


@dispatch
def render_node(node: Node, **args):
    return render_node(node, tags.Tag[node.tag](), **args)


@dispatch
def render_node(node: SequenceNode, tag: tags.Tag, **args):
    """Render seq nodes"""
    subargs = args.copy()

    out = []
    for subvaluenode in get_values(node):
        subtag = tags.Tag[subvaluenode.tag]()
        subvalue = render_node(subvaluenode, subtag, **subargs)
        out.append(subvalue)

    return out


@dispatch
def render_node(node: MappingNode, tag: tags.Map, **args):
    """Render map nodes"""
    subargs = args.copy()

    out = {}
    for subkeynode, subvaluenode in get_items(node):
        subkey = render_node(subkeynode)
        subargs["key"] = subkeynode
        subtag = tags.Tag[subvaluenode.tag]()
        subvalue = render_node(subvaluenode, subtag, **subargs)
        out[subkey] = subvalue

    return out


@dispatch
def render_node(cfg: "RootConfig"):
    """Render the resulting node of merging all entries"""

    from gamma.config.merge import merge_nodes
    from functools import reduce

    nodes = list(cfg._root_nodes.values())
    _, node = merge_nodes(nodes)
    return render_node(node, config=cfg)


@dispatch
def render_node(cfg: "ConfigNode", dump=True):
    """Render the config node. Defaults to "dump mode"!

    Args:
        dump: If true, assume it's "dump mode" where secrets are not to be rendered.
    """
    return render_node(cfg._node, config=cfg, dump=dump)


from . import builtin_tags  # noqa
from gamma.config.confignode import ConfigNode, RootConfig  # noqa

