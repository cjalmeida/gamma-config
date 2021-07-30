from gamma.config.confignode import ConfigNode
from gamma.dispatch import dispatch
from ruamel.yaml.nodes import MappingNode, SequenceNode

from .render import render_node
from .tags import Map, Seq


def _prepare_ctx(**ctx):
    from gamma.config import get_config

    ctx.setdefault("recursive", True)
    ctx.setdefault("config", get_config())
    return ctx


@dispatch
def to_dict(node, **ctx):
    """Converts a node to a dictionary."""
    ctx = _prepare_ctx(**ctx)
    return render_node(node, **ctx)


@dispatch
def to_dict(node: ConfigNode, **ctx):
    """Converts a ConfigNode to a dictionary."""
    ctx.setdefault("config", node)
    ctx = _prepare_ctx(**ctx)
    return render_node(node, **ctx)


@dispatch
def to_dict(node: MappingNode, **ctx):
    """Render MappingNodes as dict regardless of tag value"""
    ctx = _prepare_ctx(**ctx)
    return render_node(node, Map(), **ctx)


@dispatch
def to_dict(node: SequenceNode, **ctx):
    """Render SequenceNodes as list regardless of tag value"""
    ctx = _prepare_ctx(**ctx)
    return render_node(node, Seq(), **ctx)
