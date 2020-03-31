"""Implements the dictionary merging functionality"""

from copy import deepcopy
from typing import Mapping


def merge(target, patch):
    """This will merge ``target`` inplace by applying ``patch``"""

    for key in patch:
        patch_val = patch[key]
        target_val = target.get(key)

        # handle new keys
        if key not in target:
            target[key] = deepcopy(patch_val)

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
