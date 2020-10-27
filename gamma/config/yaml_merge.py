"""Implements the dictionary merging functionality"""

from copy import deepcopy
from typing import Mapping, Optional

from ruamel.yaml.comments import CommentedBase
import itertools


def merge(target, patch):
    """This will merge ``target`` inplace by applying ``patch``"""

    for key in patch:
        patch_val = patch[key]
        target_val = target.get(key)
        hint = _get_hint(patch_val)

        # handle new keys
        if key not in target:
            target[key] = deepcopy(patch_val)

        # check for any merge hints
        elif hint and hint == "merge_replace":
            target[key] = patch_val

        # handle list merge
        elif isinstance(target_val, list) and isinstance(patch_val, list):

            # compare items and append if needed
            for patch_item in patch_val:
                if patch_item in target_val:
                    continue
                target_val.append(deepcopy(patch_item))

        elif isinstance(target_val, Mapping) and isinstance(patch_val, Mapping):
            merge(target_val, patch_val)

        else:
            target[key] = deepcopy(patch_val)


def _get_hint(val) -> Optional[str]:
    if isinstance(val, CommentedBase):
        stack = [val.ca.comment]
        comments = []

        # flatten comment hierarchy. can't use itertools.chain here :(
        while stack:
            item = stack.pop(0)
            if item and hasattr(item, "value"):
                comments.append(item)
            elif isinstance(item, list):
                for sub in item:
                    if sub:
                        stack.append(sub)

        for cm in comments:
            if cm.value:
                line = cm.value.strip().lstrip("#").strip()
                if line.startswith("@hint:"):
                    hint = line[6:].strip()
                    return hint

    return None
