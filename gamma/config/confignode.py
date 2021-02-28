from functools import reduce
from gamma.config.load import load_node
from gamma.dispatch import dispatch
from typing import Dict, NamedTuple, Optional
from ruamel.yaml.nodes import MappingNode, Node, SequenceNode
from .rawnodes import get_entry, get_keys, get_values, union_nodes
from .render import render_node
from .tags import Tag
from .merge import merge_nodes
from . import tags
import collections


class ConfigNode(collections.Mapping):
    def __init__(self, node: MappingNode, root=Optional["RootConfig"]) -> None:
        self._node = node
        self._root = root

    def __getitem__(self, key):
        ctx = dict(root=self._root, config=self, dump=False)
        return config_getitem(self, key, **ctx)

    def __iter__(self):
        return ((render_node(key), self[key]) for key in get_keys(self))

    def __len__(self) -> int:
        return config_len(self)

    def __getattr__(self, key):
        if key.startswith("_"):
            return object.__getattribute__(self, key)

        try:
            return self[key]
        except KeyError:
            empty = MappingNode(tags.Map, [])
            return ConfigNode(empty, self._root)


class RootKey(NamedTuple):
    name: str

    def __repr__(self) -> str:
        return f"RootKey({self.name})"

    def __str__(self) -> str:
        return self.name


class RootConfig(ConfigNode):
    def __init__(self, entry_key: Optional[str] = None, entry=None) -> None:
        """Initialize the root config with optionally a default entry"""
        self._root_nodes: Dict[str, MappingNode] = dict()
        super().__init__(None, self)

        if entry_key is not None:
            if entry is None:
                raise ValueError("Missing 'entry' argument")
            push_entry(self, entry_key, entry)


@dispatch
def push_entry(root: RootConfig, entry_key: str, entry) -> None:
    node = load_node(entry)
    push_entry(root, entry_key, node)


@dispatch
def push_entry(root: RootConfig, entry_key: str, node: Node) -> None:
    if entry_key in root._root_nodes:
        raise ValueError(f"Config file/entry named {entry_key} duplicated.")
    root._root_nodes[entry_key] = node


@dispatch
def config_getitem(cfg: ConfigNode, key, **ctx):
    _key, _item = get_entry(cfg._node, key)
    ctx = ctx.copy()
    ctx["key"] = _key
    return config_getitem(_item, **ctx)


@dispatch
def config_getitem(cfg: RootConfig, key, **ctx):
    # search recursily on root nodes for an item matching
    matches = []
    key: str
    node: Node

    for entry_key, node in cfg._root_nodes.items():
        subkey, subnode = get_entry(node, key, default=None)
        if subnode:
            matches.append((RootKey(entry_key), subkey, subnode))

    if len(matches) > 1:
        key, node = reduce(merge_nodes, matches)
    elif len(matches) == 1:
        _, key, node = matches[0]
    else:
        raise KeyError(key)

    return config_getitem(node, key=key, **ctx)


@dispatch
def config_getitem(item: Node, **ctx):
    tag = Tag[item.tag]()
    return render_node(item, tag, **ctx)


@dispatch
def config_getitem(item: MappingNode, **ctx):
    return ConfigNode(item, ctx["root"])


@dispatch
def config_getitem(item: SequenceNode, **ctx):
    out = []
    for sub in get_values(item):
        out.append(config_getitem(sub, **ctx))
    return out


@dispatch
def get_keys(cfg: ConfigNode):
    return get_keys(cfg._node)


@dispatch
def get_keys(cfg: RootConfig):
    returned = set()
    for node in cfg._root_nodes:
        for key in get_keys(node):
            if key in returned:
                continue
            returned.add(key)
            yield key


@dispatch
def config_len(cfg: ConfigNode):
    return len(cfg._node.value)


@dispatch
def config_len(cfg: RootConfig):
    return len(list(get_keys(cfg)))

