from gamma.config.load import load_node
from gamma.dispatch import dispatch
from typing import Dict, NamedTuple, Optional
from ruamel.yaml.nodes import MappingNode, Node, SequenceNode
from .rawnodes import get_entry, get_keys, get_values
from .tags import Tag
from .merge import merge_nodes
from . import tags
import collections


class ConfigNode(collections.Mapping):
    def __init__(
        self, node: MappingNode, root=Optional["RootConfig"], key=None
    ) -> None:

        self._node = node
        self._root = root
        self._key = key

    def __getitem__(self, key):
        ctx = dict(root=self._root, config=self, dump=False)
        return config_getitem(self, key, **ctx)

    def __iter__(self):
        from .render import render_node
        return (render_node(key) for key in get_keys(self))

    def __len__(self) -> int:
        return config_len(self)

    def __getattr__(self, key):
        if key.startswith("_"):
            return object.__getattribute__(self, key)

        try:
            return self[key]
        except KeyError:
            empty = MappingNode(tags.Map, [])
            return ConfigNode(empty, self._root, key=key)

    def __call__(self, *args, **kwds):
        raise TypeError(
            "A ConfigNode object is not callable. Are you're trying to "
            f"access the empty/undefined key '{self._key}'?"
        )


class RootConfig(ConfigNode):
    def __init__(self, entry_key: Optional[str] = None, entry=None) -> None:
        """Initialize the root config with optionally a default entry

        New entries should be inserted with the ``push_entry`` function.
        The entries are always iterated in ``entry_key`` lexicographical
        sort order and this affects merge results.

        """
        self._root_nodes: Dict[str, MappingNode] = collections.OrderedDict()
        super().__init__(node=None, root=self)

        if entry_key is not None:
            if entry is None:
                raise ValueError("Missing 'entry' argument")
            push_entry(self, entry_key, entry)


@dispatch
def push_entry(root: RootConfig, entry_key: str, entry, content_type=None) -> None:
    """Add an entry to the root config.

    The entry itself can be of any supported format by ``load_node``. You can
    disambiguate between string/bytes values by providing an optional ``content_type``
    """
    node = load_node(entry, content_type)
    push_entry(root, entry_key, node)


@dispatch
def push_entry(root: RootConfig, entry_key: str, node: Node) -> None:
    if entry_key in root._root_nodes:
        raise ValueError(f"Config file/entry named {entry_key} duplicated.")

    d = root._root_nodes
    d[entry_key] = node

    # sort by entry_key
    s = collections.OrderedDict(sorted(d.items(), key=lambda x: x[0]))
    root._root_nodes = s


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
            # append entry to the node comment
            matches.append((subkey, subnode))

    if matches:
        key, node = merge_nodes(matches)
    else:
        raise KeyError(key)

    return config_getitem(node, key=key, **ctx)


@dispatch
def config_getitem(item: Node, **ctx):
    from .render import render_node

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
    for node in cfg._root_nodes.values():
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

