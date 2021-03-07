from ruamel.yaml.nodes import MappingNode, SequenceNode
from gamma.dispatch import dispatch
from .render import render_node
from .tags import Map, Seq


@dispatch
def to_dict(node):
    """Converts a node to a dictionary"""
    return render_node(node)


@dispatch
def to_dict(node: MappingNode):
    """Render MappingNodes as dict regardless of tag value"""
    return render_node(node, Map())


@dispatch
def to_dict(node: SequenceNode):
    """Render SequenceNodes as list regardless of tag value"""
    return render_node(node, Seq())
