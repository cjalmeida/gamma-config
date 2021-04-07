import copy
from io import StringIO

from gamma.dispatch import dispatch
from ruamel.yaml import YAML
from ruamel.yaml.nodes import MappingNode, ScalarNode, SequenceNode

from .confignode import ConfigNode, RootConfig
from .merge import merge_nodes
from .rawnodes import as_node
from .render import render_node
from .tags import Tag


def yaml_serialize(node):
    with StringIO() as stream:
        yaml = YAML(typ="rt")
        yaml.serialize(node, stream)
        stream.seek(0)
        return stream.read()


@dispatch
def to_yaml(cfg: RootConfig, resolve_tags: bool):
    """Dump a config/node to the YAML representation.

    Args:
        resolve_tags: if True, will render tags, otherwise, dump tags unrendered.
    """

    nodes = list(cfg._root_nodes.values())
    _, node = merge_nodes(nodes)
    if resolve_tags:
        node = dump_node(node, config=cfg)
    return yaml_serialize(node)


@dispatch
def to_yaml(cfg: ConfigNode, resolve_tags: bool):
    node = cfg._node
    if resolve_tags:
        node = dump_node(node, config=cfg)
    return yaml_serialize(node)


@dispatch
def to_yaml(cfg: ConfigNode):
    """Render a ConfigNode assuming default of `resolve_tags` = True"""
    return to_yaml(cfg, True, config=cfg)


@dispatch
def dump_node(node: ScalarNode, *, config=None):
    """Dump a `scalar` node as raw YAML node"""
    tag: str = node.tag
    if not tag.startswith("tag:yaml.org,2002:"):
        tagobj = Tag[tag]()
        val = render_node(node, tagobj, dump=True, config=config)
        return as_node(val)
    return node


@dispatch
def dump_node(node: SequenceNode, *, config=None):
    """Dump a `seq` node as raw YAML node"""

    tag: str = node.tag

    # render if sequence itself is tagged
    if not tag.startswith("tag:yaml.org,2002:"):
        tagobj = Tag[tag]()
        val = render_node(node, tagobj, dump=True, config=config)
        return as_node(val)

    # resolve recursively for each value
    newvalue = [dump_node(v, config=config) for v in node.value]
    node = copy.copy(node)
    node.value = newvalue
    return node


@dispatch
def dump_node(node: MappingNode, *, config=None):
    """Dump a `scalar` node as raw YAML node"""
    tag: str = node.tag

    # render if sequence itself is tagged
    if not tag.startswith("tag:yaml.org,2002:"):
        tagobj = Tag[tag]()
        val = render_node(node, tagobj, dump=True, config=config)
        return as_node(val)

    # resolve recursively for each entry
    newvalue = [(k, dump_node(v, config=config)) for (k, v) in node.value]
    node = copy.copy(node)
    node.value = newvalue
    return node
