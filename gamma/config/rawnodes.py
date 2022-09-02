"""Module implementing convenience methods for dealing with `ruamel.yaml` `Node`s"""
from typing import Any, Hashable, Iterable, Optional, Tuple

from gamma.dispatch import dispatch
from ruamel.yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

Entry = Tuple[Node, Optional[Node]]


@dispatch
def get_keys(node: MappingNode) -> Iterable[Node]:
    """Get all keys on a `map` node"""
    for item_key, _ in node.value:
        yield item_key


@dispatch
def get_item(node: MappingNode, key, *, default=...) -> Node:
    """Get a single child node item from `map` node"""
    for item_key, item_value in node.value:
        if is_equal(key, item_key):
            return item_value

    if default is not Ellipsis:
        return default

    raise KeyError(key)  # pragma: no cover


@dispatch
def get_entry(node: MappingNode, key, *, default=...) -> Entry:
    """Get a (key, value) entry from a `map` node.

    Args:
        default: return this value instead of `KeyError` if not found.

    Raise:
        `KeyError` if key not found and `default` not provided
    """
    for item_key, item_value in node.value:
        if is_equal(key, item_key):
            return item_key, item_value

    if default is not Ellipsis:
        return as_node(key), default

    raise KeyError(key)


@dispatch
def is_equal(a, b) -> bool:
    """Check if `a` is equal to `b`"""
    return a == b


@dispatch
def is_equal(a: SequenceNode, b: SequenceNode) -> bool:
    """Check if `a` is equal to `b`"""
    a_values = get_values(a)
    b_values = get_values(b)
    for value in a_values:
        if value not in b_values:
            return False
    return True


@dispatch
def is_equal(a: MappingNode, b: MappingNode) -> bool:
    """Check if `a` is equal to `b`"""
    if a.tag != b.tag:
        return False
    a_keys = get_keys(a)
    b_keys = get_keys(b)
    for key in union_nodes(a_keys, b_keys):
        _, a_entry = get_entry(a, key, default=None)
        _, b_entry = get_entry(b, key, default=None)
        if a_entry is None or b_entry is None or not is_equal(a_entry, b_entry):
            return False
    return True


@dispatch
def is_equal(a: ScalarNode, b) -> bool:
    """Check if `a` is equal to `b`"""
    return is_equal(a, as_node(b))


@dispatch
def is_equal(a, b: ScalarNode) -> bool:
    """Check if `a` is equal to `b`"""
    return is_equal(as_node(a), b)


@dispatch
def is_equal(a: ScalarNode, b: ScalarNode):
    return a.tag == b.tag and a.value == b.value


@dispatch
def as_node(a: Node) -> Node:
    return a


@dispatch
def as_node(a) -> Node:
    """Return the `Node` representation of a given object.

    This method handle basic scalar types.
    """

    # handle base types
    if isinstance(a, str):
        return ScalarNode("tag:yaml.org,2002:str", value=a)
    elif isinstance(a, bool):
        return ScalarNode("tag:yaml.org,2002:bool", value=str(a))
    elif isinstance(a, int):
        return ScalarNode("tag:yaml.org,2002:int", value=str(a))
    elif isinstance(a, float):
        return ScalarNode("tag:yaml.org,2002:float", value=str(a))
    elif a is None:
        return ScalarNode("tag:yaml.org,2002:null", value="null")
    else:
        raise Exception(f"Can't handle type {type(a)} for value {a}")


@dispatch
def get_id(a) -> Hashable:
    # fallback
    return a


@dispatch
def get_id(a: ScalarNode) -> Hashable:
    """Return an object that allows to ScalarNodes to be hashed and compared"""
    return (a.tag, a.value)


@dispatch
def is_in(node: Node, container: Iterable[Any]) -> bool:
    """Return true if `node` is in `container`"""
    for item in container:
        if is_equal(item, node):
            return True
    return False


@dispatch
def get_entries(node: MappingNode) -> Iterable[Entry]:
    """Return all entries (key, value) in this `map` node"""
    for item_key, item_value in node.value:
        yield item_key, item_value


@dispatch
def get_values(node: SequenceNode) -> Iterable[Node]:
    """Return all values in this `seq` node"""
    for item_value in node.value:
        yield item_value


@dispatch
def get_values(node: MappingNode) -> Iterable[Node]:
    """Return all values in this `map` node"""
    for _, item_value in node.value:
        yield item_value


@dispatch
def union_nodes(first: Iterable, second: Iterable) -> Iterable:
    """Union two sets of nodes.

    By default we keep the ones in `first` if equals."""

    out = dict()

    for a in first:
        out[get_id(a)] = a

    for b in second:
        if b not in out:
            out[get_id(b)] = b

    return list(out.values())
