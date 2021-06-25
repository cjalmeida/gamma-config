"""Module for loading content as `ruamel.yaml` `Node` instances"""
from io import IOBase, StringIO
from pathlib import Path
from typing import Dict

from gamma.dispatch import dispatch, parametric
from ruamel.yaml.nodes import Node


@parametric
class ContentType:
    pass


YAMLContent = ContentType["text/yaml"]


@dispatch
def load_node(val: str, content_type=None) -> Node:
    """Load a string as `Node`, defaults to YAML content"""
    stream = StringIO(val)
    stream.seek(0)
    return load_node(stream, content_type)


@dispatch
def load_node(stream: IOBase, content_type=None) -> Node:
    """Load a stream as `Node`, defaults to YAML content"""
    content_type = content_type or YAMLContent()
    return load_node(stream, content_type)


@dispatch
def load_node(stream: IOBase, _: YAMLContent) -> Node:
    """Load a YAML stream"""
    from ruamel.yaml import YAML

    yaml = YAML()
    const, _ = yaml.get_constructor_parser(stream)
    node = const.composer.get_single_node()
    return node


@dispatch
def load_node(entry: Path, content_type=None) -> Node:
    """Load path's content, defaults to YAML content"""
    try:
        content: str = entry.read_text().strip()
        if not content:
            return load_node({})
        return load_node(content, content_type)
    except Exception as ex:
        raise ValueError(f"Error loading from file '{entry}'") from ex


@dispatch
def load_node(val: Dict, content_type=None) -> Node:
    """Load dict as node"""
    from ruamel.yaml import YAML

    if not val:
        val = dict()
    yaml = YAML()
    stream = StringIO()
    yaml.dump(val, stream)
    stream.seek(0)
    content = stream.read()
    return load_node(content, YAMLContent())
