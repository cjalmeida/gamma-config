import pdb
import copy
from functools import reduce
from ruamel.yaml.compat import StringIO

from ruamel.yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode
from ruamel.yaml.serializer import Serializer

from gamma.dispatch import dispatch

from . import Tag, render_node
from .confignode import ConfigNode, RootConfig
from .merge import merge_nodes
from .rawnodes import as_node


@dispatch
def to_yaml(cfg: RootConfig, *, resolve_tags=False):
    """Dump a config/node to the YAML representation.

    Args:
        resolve_tags: if True, will render tags, otherwise, dump tags unrendered.
    """
    nodes = list(cfg._root_nodes.values())
    _, node = merge_nodes(nodes)
    return to_yaml(node, resolve_tags=resolve_tags, config=cfg)


@dispatch
def to_yaml(cfg: ConfigNode, *, resolve_tags=False):
    return to_yaml(cfg._node, resolve_tags=resolve_tags, config=cfg)


@dispatch
def to_yaml(node: Node, *, resolve_tags=False, config=None):
    from ruamel.yaml.main import serialize

    if resolve_tags:
        node = resolve_node(node, config=config)

    return serialize(node)




@dispatch
def resolve_node(node: ScalarNode, *, config=None):
    tag: str = node.tag
    if not tag.startswith("tag:yaml.org,2002:"):
        tagobj = Tag[tag]()
        val = render_node(node, tagobj, dump=True, config=config)
        return as_node(val)
    return node


@dispatch
def resolve_node(node: SequenceNode, *, config=None):
    tag: str = node.tag

    # render if sequence itself is tagged
    if not tag.startswith("tag:yaml.org,2002:"):
        tagobj = Tag[tag]()
        val = render_node(node, tagobj, dump=True, config=config)
        return as_node(val)

    # resolve recursively for each value
    newvalue = [resolve_node(v, config=config) for v in node.value]
    node = copy.copy(node)
    node.value = newvalue
    return node


@dispatch
def resolve_node(node: MappingNode, *, config=None):
    tag: str = node.tag

    # render if sequence itself is tagged
    if not tag.startswith("tag:yaml.org,2002:"):
        tagobj = Tag[tag]()
        val = render_node(node, tagobj, dump=True, config=config)
        return as_node(val)

    # resolve recursively for each entry
    newvalue = [(k, resolve_node(v, config=config)) for (k, v) in node.value]
    node = copy.copy(node)
    node.value = newvalue
    return node
