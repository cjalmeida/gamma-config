from gamma.dispatch import dispatch
from ruamel.yaml.nodes import MappingNode, SequenceNode

from .render import render_node
from .tags import Map, Seq


@dispatch
def to_dict(node, **ctx):
    """Converts a node to a dictionary"""
    return render_node(node, **ctx)


@dispatch
def to_dict(node: MappingNode, **ctx):
    """Render MappingNodes as dict regardless of tag value"""
    return render_node(node, Map(), **ctx)


@dispatch
def to_dict(node: SequenceNode, **ctx):
    """Render SequenceNodes as list regardless of tag value"""
    return render_node(node, Seq(), **ctx)
