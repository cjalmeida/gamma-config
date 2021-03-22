"""Implements the node merging functionality"""
import re
from copy import deepcopy
from functools import reduce
from typing import List, Tuple, Union

from gamma.dispatch import dispatch
from ruamel.yaml.nodes import MappingNode, Node, SequenceNode

from .rawnodes import get_item, get_keys, get_values, is_in, union_nodes

hints_pattern = re.compile("^.*@hint: *?([A-Za-z0-9_]+) ?.*$")


@dispatch
def merge_nodes(nodes: List):
    """Merge nodes iterable, ignoring key"""
    if len(nodes) == 0:
        raise ValueError("Empty nodes list")
    elif len(nodes) == 1 and isinstance(nodes[0], Tuple):
        return nodes[0]
    elif len(nodes) == 1 and isinstance(nodes[0], Node):
        return None, nodes[0]
    return reduce(merge_nodes, nodes)


@dispatch
def merge_nodes(l_node: MappingNode, r_node: MappingNode):
    """Merge map nodes ignoring key"""
    return merge_nodes(None, l_node, None, r_node)


@dispatch
def merge_nodes(left: Tuple, r_node: MappingNode):
    """Merge map nodes ignoring key (for assymetric fold-left)"""
    l_node = left[-1]
    return merge_nodes(None, l_node, None, r_node)


@dispatch
def merge_nodes(left: Tuple, right: Tuple):
    """Merge map nodes (symetric fold-left)

    Args:
        left, right: Tuple of (key: Node, value: Node)
    """

    l_key, l_node = left
    r_key, r_node = right
    return merge_nodes(l_key, l_node, r_key, r_node)


@dispatch
def merge_nodes(l_key, l_node: Union[None, Node], r_key, r_node: Union[None, Node]):
    """Merge scalars.

    Return "right", or "left" if "right" is `None`
    """
    # scalars,
    if r_node is not None:
        return r_key, r_node
    else:
        return l_key, l_node


@dispatch
def merge_nodes(l_key, l_node: MappingNode, r_key, r_node: MappingNode):
    """Merge `map` nodes recursively.

    Right side has precedence. `@hint: merge_replace` overrides merging, returning
    right.
    """
    if has_replace_hint(r_node):
        return r_key, r_node

    newvalue = []
    # Merge if both nodes are mappings
    l_keys = get_keys(l_node)
    r_keys = get_keys(r_node)
    subkeys = union_nodes(r_keys, l_keys)
    for subkey in subkeys:
        l_subnode = get_item(l_node, subkey, default=None)
        r_subnode = get_item(r_node, subkey, default=None)
        _, subvalue = merge_nodes(subkey, l_subnode, subkey, r_subnode)
        newvalue.append((subkey, subvalue))

    # by default, we use right side meta data
    newnode = deepcopy(r_node)
    newnode.value = newvalue
    return r_key, newnode


@dispatch
def merge_nodes(l_key, l_node: SequenceNode, r_key, r_node: SequenceNode):
    """Merge `sequence` nodes recursively.

    Right side has precedence. `@hint: merge_replace` overrides merging, returning
    right.
    """

    if has_replace_hint(r_node):
        return r_key, r_node

    newvalue = list(get_values(l_node)).copy()
    for r_item in get_values(r_node):
        if not is_in(r_item, newvalue):
            newvalue.append(r_item)

    # by default, we use right side meta data
    newnode = deepcopy(r_node)
    newnode.value = newvalue
    return r_key, newnode


@dispatch
def has_replace_hint(node: Node) -> bool:
    """Check for existence of config "hint" in the node's comments.

    Only `@hint: merge_replace` is supported.
    """

    node_comments = getattr(node, "comment", [])
    if not node_comments:
        return False

    # flatten comment hierarchy. can't use itertools.chain here :(
    hints = set()
    stack = [node_comments]
    while stack:
        item = stack.pop(0)

        if item and hasattr(item, "value"):
            match = hints_pattern.match(item.value)
            if match:
                hints.add(match.group(1))

        elif isinstance(item, list):
            for sub in item:
                if sub:
                    stack.append(sub)

    return "merge_replace" in hints
