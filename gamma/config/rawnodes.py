from typing import Iterable, Optional, Tuple
from ruamel.yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode
from ruamel.yaml.tokens import CommentToken
from gamma.dispatch import dispatch
from functools import reduce


def append_comment(node: Node, comment: str):
    if not node.comment:
        node.comment = []
    token = CommentToken("#" + comment, 0, 0)
    node.comment.append(token)


@dispatch
def get_keys(node: MappingNode):
    for item_key, _ in node.value:
        yield item_key


@dispatch
def get_item(node: MappingNode, key, default=...):
    for item_key, item_value in node.value:
        if is_equal(key, item_key):
            return item_value

    if default is not Ellipsis:
        return default

    raise KeyError(key)


@dispatch
def get_entry(node: MappingNode, key, default=...) -> Tuple[Node, Optional[Node]]:
    for item_key, item_value in node.value:
        if is_equal(key, item_key):
            return item_key, item_value

    if default is not Ellipsis:
        return as_node(key), default

    raise KeyError(key)


@dispatch
def is_equal(a: ScalarNode, b):
    return is_equal(a, as_node(b))


@dispatch
def is_equal(a, b: ScalarNode):
    return is_equal(as_node(a), b)


@dispatch
def as_node(a: str):
    return ScalarNode("tag:yaml.org,2002:str", value=a)


@dispatch
def is_equal(a: ScalarNode, b: ScalarNode):
    return a.tag == b.tag and a.value == b.value


@dispatch
def get_id(a):
    return a


@dispatch
def get_id(a: ScalarNode):
    return (a.tag, a.value)


@dispatch
def is_in(node: Node, container):
    for item in container:
        if is_equal(item, node):
            return True
    return False


@dispatch
def get_items(node: MappingNode) -> Iterable[Node]:
    for item_key, item_value in node.value:
        yield item_key, item_value


@dispatch
def get_values(node: SequenceNode) -> Iterable[Node]:
    for item_value in node.value:
        yield item_value


@dispatch
def get_values(node: MappingNode) -> Iterable[Node]:
    for _, item_value in node.value:
        yield item_value


@dispatch
def union_nodes(first: Iterable, second: Iterable):
    """Union two sets of nodes.

    By default we keep the ones in `first` if equals."""

    out = dict()

    for a in first:
        out[get_id(a)] = a

    for b in second:
        if b not in out:
            out[get_id(b)] = b

    return list(out.values())


@dispatch
def union_nodes(nodes: Iterable):
    reduce(union_nodes, nodes)
