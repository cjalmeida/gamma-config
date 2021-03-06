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
    stream = StringIO(val)
    stream.seek(0)
    return load_node(stream, content_type)


@dispatch
def load_node(stream: IOBase, content_type=None) -> Node:
    """Load YAML data"""
    content_type = content_type or YAMLContent()
    return load_node(stream, content_type)


@dispatch
def load_node(stream: IOBase, _: YAMLContent) -> Node:
    from ruamel.yaml import YAML

    yaml = YAML()
    const, _ = yaml.get_constructor_parser(stream)
    node = const.composer.get_single_node()
    return node


@dispatch
def load_node(entry: Path, content_type=None):
    content: str = entry.read_text().strip()
    if not content:
        return None
    return load_node(content, content_type)


@dispatch
def load_node(val: Dict, content_type=None):
    from ruamel.yaml import YAML

    yaml = YAML()
    stream = StringIO()
    yaml.dump(val, stream)
    stream.seek(0)
    content = stream.read()
    if not content:
        return None
    return load_node(content, content_type)
