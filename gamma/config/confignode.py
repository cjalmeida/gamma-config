import collections
import re
from contextlib import contextmanager
from typing import Any, Dict, Iterable, Optional

from gamma.config.load import load_node
from gamma.dispatch import dispatch
from ruamel.yaml.nodes import MappingNode, Node, SequenceNode

from . import tags
from .merge import merge_nodes
from .rawnodes import get_entry, get_id, get_keys, get_values
from .tags import Tag

SAFE_ENTRY_KEY = re.compile("^[A-Za-z0-9].+$")


class ConfigNode(collections.abc.Mapping):
    """Represent a dict-like config object.

    `ConfigNode` is immutable, changes should be made to the source `RootConfig`
    object. This class should be safe to pickle and pass to subprocesses.

    You when accessing keys by attribute `eg: config.foo` they'll return an empty
    `ConfigNode` instead of raising an `AttributeError`.


    """

    def __init__(
        self,
        node: MappingNode,
        root: Optional["RootConfig"] = None,
        parent: Optional["ConfigNode"] = None,
        key=None,
    ) -> None:
        """
        Args:
            node: the backing `MappingNode`
            root: the root of the config tree
            key: the node key in the config tree
        """

        self._node = node
        self._root = root
        self._key = key
        self._frozen = True
        self._parent = parent

    def __getitem__(self, key):
        ctx = dict(config=self, dump=False)
        return config_getitem(self, key, **ctx)

    def __iter__(self):  # pragma: no cover
        from .render import render_node

        return (render_node(key) for key in get_keys(self))

    def __len__(self) -> int:
        return config_len(self)

    def __getattr__(self, key):
        if key.startswith("__"):
            return object.__getattribute__(self, key)

        try:
            return self[key]
        except KeyError as err:
            raise AttributeError(key) from err

    def __call__(self, *args, **kwds):
        raise TypeError(
            "A ConfigNode object is not callable. Are you're trying to "
            f"access the empty/undefined key '{self._key}'?"
        )

    def __setattr__(self, name: str, value: Any) -> None:
        if not name[0] == "_":
            raise TypeError(
                f"'{self.__class__.__name__}' object does not support item assignment"
            )
        else:
            object.__setattr__(self, name, value)


class RootConfig(ConfigNode):
    """A root config object.

    The object is a collection of `(entry_key: str, entry: Node)`, sorted by
    the `entry_key`. A item access will search for the key in each entry and merge
    those found.

    New entries should be inserted with the push_entry` function.
    The entries are always iterated in `entry_key` lexicographical
    sort order and this affects merge results.
    """

    def __init__(self, entry_key: Optional[str] = None, entry=None) -> None:
        """
        Initialize the object, optionally adding a single entry. See
        [`push_entry`](api?id=push_entry).
        """
        self._root_nodes: Dict[str, MappingNode] = collections.OrderedDict()
        super().__init__(node=None, root=self, parent=None)

        if entry_key is not None:
            if entry is None:
                raise ValueError("Missing 'entry' argument")
            push_entry(self, entry_key, entry)


@dispatch
def push_entry(
    root: RootConfig, entry_key: str, entry, *, _allow_unsafe=False, content_type=None
) -> None:
    """Add an entry to the root config.

    The entry itself can be of any supported format by ``load_node``. You can
    disambiguate between string/bytes values by providing an optional ``content_type``
    """
    node = load_node(entry, content_type)
    push_entry(root, entry_key, node, _allow_unsafe=_allow_unsafe)


@dispatch
def push_entry(
    root: RootConfig, entry_key: str, node: Node, *, _allow_unsafe=False
) -> None:
    """Add a `Node` entry to the root config object.

    Entries are loaded in sorted order.

    Note: the global root object can only be modified by the thread that created it.
    """

    from .globalconfig import check_can_modify

    check_can_modify(root)

    if (not _allow_unsafe) and (not SAFE_ENTRY_KEY.match(entry_key)):
        pat = SAFE_ENTRY_KEY.pattern
        raise ValueError(f"Invalid entry_key: '{entry_key}'. Should match {pat}.")

    if entry_key in root._root_nodes:
        raise ValueError(f"Config file/entry named {entry_key} duplicated.")

    d = root._root_nodes
    d[entry_key] = node

    # sort by entry_key
    s = collections.OrderedDict(sorted(d.items(), key=lambda x: x[0]))
    root._root_nodes = s


@dispatch
def remove_entry(cfg: RootConfig, entry_key: str):
    """Remove an entry from the RootConfig object."""
    del cfg._root_nodes[entry_key]


@dispatch
def config_getitem(cfg: ConfigNode, key, **ctx):
    """Get an item from config by key."""
    _key, _item = get_entry(cfg._node, key)
    ctx = ctx.copy()
    ctx["key"] = _key
    return resolve_item(_item, **ctx)


@dispatch
def config_getitem(cfg: RootConfig, key, **ctx):
    """Get an item from a root config by key.

    We find all entries matching the key and merge them dynamically using
    `merge_nodes`.
    """
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

    return resolve_item(node, key=key, **ctx)


@dispatch
def resolve_item(item: Node, **ctx):
    """Resolve a config item from a ruamel.yaml `Node`

    This method delegates to a more specific method dispatched on (Node, Tag) types
    """
    tag = Tag[item.tag]()
    return resolve_item(item, tag, **ctx)


@dispatch
def resolve_item(item: Node, tag: Tag, **ctx):
    """Resolve a config item from a ruamel.yaml `Node`

    Fallback to rendering the node using `render_node`
    """

    from .render import render_node

    return render_node(item, tag, **ctx)


@dispatch
def resolve_item(item: MappingNode, tag: tags.Map, **ctx):
    """Wrap a plain `map` node as a child `ConfigNode` object"""
    cfg = ctx.get("config")
    root = cfg._root if cfg is not None else None
    return ConfigNode(item, root=root, parent=cfg)


@dispatch
def resolve_item(item: SequenceNode, tag: tags.Seq, **ctx):
    """Iterates on a `seq` node, resolving each child item node."""
    out = []
    for sub in get_values(item):
        out.append(resolve_item(sub, **ctx))
    return out


@dispatch
def get_keys(cfg: ConfigNode) -> Iterable[Node]:
    """Return all keys in a config node"""
    return get_keys(cfg._node)


@dispatch
def get_keys(cfg: RootConfig) -> Iterable[Node]:
    """Return all *distinct* keys in a config node"""
    returned = set()
    for node in cfg._root_nodes.values():
        for key in get_keys(node):
            key_id = get_id(key)
            if key_id in returned:
                continue
            returned.add(key_id)
            yield key


@dispatch
def config_len(cfg: ConfigNode) -> int:
    """Number of keys in a config node"""
    return len(cfg._node.value)


@dispatch
def config_len(cfg: RootConfig) -> int:
    """Number of *distinct* keys in a config node"""
    return len(list(get_keys(cfg)))


@dispatch
def create_last_entry_key(cfg: RootConfig) -> str:
    """Create an entry_key guaranteed to be the last entry for the object."""
    clen = config_len(cfg)
    return f"~{clen:03d}-temp"


@dispatch
@contextmanager
def config_context(cfg: RootConfig, partial) -> None:
    entry_key = create_last_entry_key(cfg)
    push_entry(cfg, entry_key, partial, _allow_unsafe=True)
    try:
        yield
    finally:
        remove_entry(cfg, entry_key)


@dispatch
@contextmanager
def config_context(partial) -> None:
    from gamma.config.globalconfig import get_config

    cfg = get_config()
    with config_context(cfg, partial):
        yield
