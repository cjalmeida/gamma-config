"""Implements the dictionary merging functionality"""

from copy import deepcopy
from typing import List, Tuple, Union

from ruamel.yaml.nodes import MappingNode, Node, SequenceNode
from gamma.dispatch import dispatch

from .rawnodes import get_keys, get_item, get_values, union_nodes, is_in
from functools import reduce


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
    """merge map nodes ignoring key"""
    return merge_nodes(None, l_node, None, r_node)


@dispatch
def merge_nodes(left: Tuple, r_node: MappingNode):
    """merge map nodes ignoring key (for assymetric fold-left)"""
    l_node = left[-1]
    return merge_nodes(None, l_node, None, r_node)


@dispatch
def merge_nodes(left: Tuple, right: Tuple):
    """merge map nodes (symetric fold-left)

    Args:
        left, right: Tuple of (key: Node, value: Node)
    """

    l_key, l_node = left
    r_key, r_node = right
    return merge_nodes(l_key, l_node, r_key, r_node)


@dispatch
def merge_nodes(l_key, l_node: Union[None, Node], r_key, r_node: Union[None, Node]):
    # scalars, return right or left if right is null
    if r_node is not None:
        return r_key, r_node
    else:
        return l_key, l_node


@dispatch
def merge_nodes(l_key, l_node: MappingNode, r_key, r_node: MappingNode):
    newvalue = []
    # Merge if both nodes are mappings
    l_keys = get_keys(l_node)
    r_keys = get_keys(r_node)
    subkeys = union_nodes(r_keys, l_keys)
    for subkey in subkeys:
        l_subnode = get_item(l_node, subkey, None)
        r_subnode = get_item(r_node, subkey, None)
        _, subvalue = merge_nodes(subkey, l_subnode, subkey, r_subnode)
        newvalue.append((subkey, subvalue))

    # by default, we use right side meta data
    newnode = deepcopy(r_node)
    newnode.value = newvalue
    return r_key, newnode


@dispatch
def merge_nodes(l_key, l_node: SequenceNode, r_key, r_node: SequenceNode):
    newvalue = list(get_values(l_node)).copy()

    for r_item in get_values(r_node):
        if not is_in(r_item, newvalue):
            newvalue.append(r_item)

    # by default, we use right side meta data
    newnode = deepcopy(r_node)
    newnode.value = newvalue
    return r_key, newnode


# def merge_nodes(target, patch):
#     """This will merge ``target`` inplace by applying ``patch``"""

#     for key in patch:
#         patch_val = patch[key]
#         target_val = target.get(key)
#         hint = _get_hint(patch_val)

#         # handle new keys
#         if key not in target:
#             target[key] = deepcopy(patch_val)

#         # check for any merge hints
#         elif hint and hint == "merge_replace":
#             target[key] = patch_val

#         # handle list merge
#         elif isinstance(target_val, list) and isinstance(patch_val, list):

#             # compare items and append if needed
#             for patch_item in patch_val:
#                 if patch_item in target_val:
#                     continue
#                 target_val.append(deepcopy(patch_item))

#         elif isinstance(target_val, Mapping) and isinstance(patch_val, Mapping):
#             merge(target_val, patch_val)

#         else:
#             target[key] = deepcopy(patch_val)


# def _get_hint(val) -> Optional[str]:
#     if isinstance(val, CommentedBase):
#         stack = [val.ca.comment]
#         comments = []

#         # flatten comment hierarchy. can't use itertools.chain here :(
#         while stack:
#             item = stack.pop(0)
#             if item and hasattr(item, "value"):
#                 comments.append(item)
#             elif isinstance(item, list):
#                 for sub in item:
#                     if sub:
#                         stack.append(sub)

#         for cm in comments:
#             if cm.value:
#                 line = cm.value.strip().lstrip("#").strip()
#                 if line.startswith("@hint:"):
#                     hint = line[6:].strip()
#                     return hint

#     return None
