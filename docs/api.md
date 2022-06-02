<a id="gamma.config"></a>

# gamma.config

<a id="gamma.config.__main__"></a>

# gamma.config.\_\_main\_\_

<a id="gamma.config.confignode"></a>

# gamma.config.confignode

<a id="gamma.config.confignode.ConfigNode"></a>

## ConfigNode Objects

```python
class ConfigNode(collections.abc.Mapping)
```

Represent a dict-like config object.

`ConfigNode` is immutable, changes should be made to the source `RootConfig`
object. This class should be safe to pickle and pass to subprocesses.

You when accessing keys by attribute `eg: config.foo` they'll return an empty
`ConfigNode` instead of raising an `AttributeError`.

<a id="gamma.config.confignode.ConfigNode.__init__"></a>

#### \_\_init\_\_

```python
def __init__(node: MappingNode, root: Optional["RootConfig"] = None, parent: Optional["ConfigNode"] = None, key=None) -> None
```

**Arguments**:

- `node` - the backing `MappingNode`
- `root` - the root of the config tree
- `key` - the node key in the config tree

<a id="gamma.config.confignode.RootConfig"></a>

## RootConfig Objects

```python
class RootConfig(ConfigNode)
```

A root config object.

The object is a collection of `(entry_key: str, entry: Node)`, sorted by
the `entry_key`. A item access will search for the key in each entry and merge
those found.

New entries should be inserted with the push_entry` function.
The entries are always iterated in `entry_key` lexicographical
sort order and this affects merge results.

<a id="gamma.config.confignode.RootConfig.__init__"></a>

#### \_\_init\_\_

```python
def __init__(entry_key: Optional[str] = None, entry=None) -> None
```

Initialize the object, optionally adding a single entry. See
[`push_entry`](api?id=push_entry).

<a id="gamma.config.confignode.push_entry"></a>

#### push\_entry

```python
@dispatch
def push_entry(root: RootConfig, entry_key: str, entry, *, _allow_unsafe=False, content_type=None) -> None
```

Add an entry to the root config.

The entry itself can be of any supported format by ``load_node``. You can
disambiguate between string/bytes values by providing an optional ``content_type``

<a id="gamma.config.confignode.push_entry"></a>

#### push\_entry

```python
@dispatch
def push_entry(root: RootConfig, entry_key: str, node: Node, *, _allow_unsafe=False) -> None
```

Add a `Node` entry to the root config object.

Entries are loaded in sorted order.

Note: the global root object can only be modified by the thread that created it.

<a id="gamma.config.confignode.remove_entry"></a>

#### remove\_entry

```python
@dispatch
def remove_entry(cfg: RootConfig, entry_key: str)
```

Remove an entry from the RootConfig object.

<a id="gamma.config.confignode.config_getitem"></a>

#### config\_getitem

```python
@dispatch
def config_getitem(cfg: ConfigNode, key, **ctx)
```

Get an item from config by key.

<a id="gamma.config.confignode.config_getitem"></a>

#### config\_getitem

```python
@dispatch
def config_getitem(cfg: RootConfig, key, **ctx)
```

Get an item from a root config by key.

We find all entries matching the key and merge them dynamically using
`merge_nodes`.

<a id="gamma.config.confignode.resolve_item"></a>

#### resolve\_item

```python
@dispatch
def resolve_item(item: Node, **ctx)
```

Resolve a config item from a ruamel.yaml `Node`

This method delegates to a more specific method dispatched on (Node, Tag) types

<a id="gamma.config.confignode.resolve_item"></a>

#### resolve\_item

```python
@dispatch
def resolve_item(item: Node, tag: Tag, **ctx)
```

Resolve a config item from a ruamel.yaml `Node`

Fallback to rendering the node using `render_node`

<a id="gamma.config.confignode.resolve_item"></a>

#### resolve\_item

```python
@dispatch
def resolve_item(item: MappingNode, tag: tags.Map, **ctx)
```

Wrap a plain `map` node as a child `ConfigNode` object

<a id="gamma.config.confignode.resolve_item"></a>

#### resolve\_item

```python
@dispatch
def resolve_item(item: SequenceNode, tag: tags.Seq, **ctx)
```

Iterates on a `seq` node, resolving each child item node.

<a id="gamma.config.confignode.get_keys"></a>

#### get\_keys

```python
@dispatch
def get_keys(cfg: ConfigNode) -> Iterable[Node]
```

Return all keys in a config node

<a id="gamma.config.confignode.get_keys"></a>

#### get\_keys

```python
@dispatch
def get_keys(cfg: RootConfig) -> Iterable[Node]
```

Return all *distinct* keys in a config node

<a id="gamma.config.confignode.config_len"></a>

#### config\_len

```python
@dispatch
def config_len(cfg: ConfigNode) -> int
```

Number of keys in a config node

<a id="gamma.config.confignode.config_len"></a>

#### config\_len

```python
@dispatch
def config_len(cfg: RootConfig) -> int
```

Number of *distinct* keys in a config node

<a id="gamma.config.confignode.create_last_entry_key"></a>

#### create\_last\_entry\_key

```python
@dispatch
def create_last_entry_key(cfg: RootConfig) -> str
```

Create an entry_key guaranteed to be the last entry for the object.

<a id="gamma.config.tags"></a>

# gamma.config.tags

Definition of base Tag class and standard YAML derived tag types

<a id="gamma.config.cache"></a>

# gamma.config.cache

Module declaring a cache utility for gamma.config

<a id="gamma.config.cache.Cache"></a>

## Cache Objects

```python
class Cache(Mapping)
```

A cache backed by a in-memory `dict`

<a id="gamma.config.cache.Cache.clear"></a>

#### clear

```python
def clear()
```

Clear cache contents

<a id="gamma.config.pydantic"></a>

# gamma.config.pydantic

<a id="gamma.config.render_cli"></a>

# gamma.config.render\_cli

<a id="gamma.config.load"></a>

# gamma.config.load

Module for loading content as `ruamel.yaml` `Node` instances

<a id="gamma.config.load.load_node"></a>

#### load\_node

```python
@dispatch
def load_node(val: str, content_type=None) -> Node
```

Load a string as `Node`, defaults to YAML content

<a id="gamma.config.load.load_node"></a>

#### load\_node

```python
@dispatch
def load_node(stream: IOBase, content_type=None) -> Node
```

Load a stream as `Node`, defaults to YAML content

<a id="gamma.config.load.load_node"></a>

#### load\_node

```python
@dispatch
def load_node(stream: IOBase, _: YAMLContent) -> Node
```

Load a YAML stream

<a id="gamma.config.load.load_node"></a>

#### load\_node

```python
@dispatch
def load_node(entry: Path, content_type=None) -> Node
```

Load path's content, defaults to YAML content

<a id="gamma.config.load.load_node"></a>

#### load\_node

```python
@dispatch
def load_node(val: Dict, content_type=None) -> Node
```

Load dict as node

<a id="gamma.config.render"></a>

# gamma.config.render

Base render_node methods

<a id="gamma.config.render.render_node"></a>

#### render\_node

```python
@dispatch
def render_node(node: Node, tag: tags.Tag, *, key: Optional[Node] = None, config: "ConfigNode" = None, dump: bool = False, recursive: bool = False, path: Optional[str] = None)
```

Spec for tag handling functions.

This function is dispatched first on the specific (Node, Tag) types. If the tag
name contains a `:` (colon) character, the tag name is interpreted as a URI and
we fallback to dispatching by the "scheme" portion of the URI and add an extra
`path` kwarg to the method call. Example:


Will be dispatched solely on (ScalarNode, Tag["!mytag"]) types. Whereas


Will first be dispatched on (ScalarNode, Tag["!mytag:bar"]), then on
(ScalarNode, Tag["!mytag"]), the last one with the optional `path` kwargs filled
as `bar`

```
foo: !mytag 1
```
```
foo: !mytag:bar 1
```

**Arguments**:

- `node` - The raw ruamel YAML node. Can be returned during a dump to keep
  the field dynamic or hide sensitive values.
- `tag` - The tag to be handled. A subinstance of ``Tag``.
  Keywork Args:
- `key` - The node key, also as a ruamel YAML node.
- `config` - The current ConfigNode object.
- `dump` - Flag indicating we're dumping the data to a potentially insecure
  destination, so sensitive data should not be returned.
- `recursive` - If true, tag handlers should recursively render nodes.
- `path` - The URI path for URI fallback dispatch
  

**Returns**:

  any value

<a id="gamma.config.render.render_node"></a>

#### render\_node

```python
@dispatch
def render_node(node: Node, **args) -> Any
```

Render node.

Construct a parameterized `Tag` class from `node.tag` and call
`render_node(Node, Tag)`

<a id="gamma.config.render.render_node"></a>

#### render\_node

```python
@dispatch
def render_node(node: ScalarNode, tag: tags.Str, **args)
```

Render scalar string

<a id="gamma.config.render.render_node"></a>

#### render\_node

```python
@dispatch
def render_node(node: ScalarNode, tag: tags.Int, **args)
```

Render scalar int

<a id="gamma.config.render.render_node"></a>

#### render\_node

```python
@dispatch
def render_node(node: ScalarNode, tag: tags.Float, **args)
```

Render scalar float

<a id="gamma.config.render.render_node"></a>

#### render\_node

```python
@dispatch
def render_node(node: ScalarNode, tag: tags.Null, **args)
```

Render scalar null

<a id="gamma.config.render.render_node"></a>

#### render\_node

```python
@dispatch
def render_node(node: ScalarNode, tag: tags.Bool, **args)
```

Render scalar boolean. Accepts YAML extended interpretation of `bool`s, like
`ruamel.yaml`

<a id="gamma.config.render.render_node"></a>

#### render\_node

```python
@dispatch
def render_node(node: ScalarNode, tag: tags.Timestamp, **args)
```

Render timestamp node as `datetime.datetime`. Use `dateutil.parser` module

<a id="gamma.config.render.render_node"></a>

#### render\_node

```python
@dispatch
def render_node(node: SequenceNode, tag: tags.Seq, **args)
```

Render `seq` nodes recursively

<a id="gamma.config.render.render_node"></a>

#### render\_node

```python
@dispatch
def render_node(node: MappingNode, tag: tags.Map, **args)
```

Render `map` nodes recursively

<a id="gamma.config.render.render_node"></a>

#### render\_node

```python
@dispatch
def render_node(cfg: "RootConfig", **args)
```

Render the resulting node of merging all entries

<a id="gamma.config.render.render_node"></a>

#### render\_node

```python
@dispatch
def render_node(cfg: "ConfigNode", **args)
```

Render the config node.

**Arguments**:

- `dump` - If true, assume it's "dump mode" where secrets are not to be rendered.

<a id="gamma.config.findconfig"></a>

# gamma.config.findconfig

Module for discovering configuration files (entries)

<a id="gamma.config.findconfig.get_entries"></a>

#### get\_entries

```python
@dispatch
def get_entries() -> List[Tuple[str, Any]]
```

Discover the config root folder and get all entries

<a id="gamma.config.findconfig.get_entries"></a>

#### get\_entries

```python
@dispatch
def get_entries(folder: Path, *, meta_include_folders=True) -> List[Tuple[str, Any]]
```

Get all entries in a given folder.

**Arguments**:

- `meta_include_folder` - If `True`, try to load the `00-meta.yaml` file in the
  folder and follow `include_folder` entries.

<a id="gamma.config.findconfig.load_meta"></a>

#### load\_meta

```python
@dispatch
def load_meta(config_root: Path) -> ConfigNode
```

Load the `00-meta.yaml` file in a given folder

<a id="gamma.config.findconfig.get_config_root"></a>

#### get\_config\_root

```python
@dispatch
def get_config_root() -> Path
```

Return the location for config root path.

The mechanisms used to find the config root are set in the ``CONFIG_LOAD_ORDER``
module variable.

<a id="gamma.config.findconfig.get_config_root"></a>

#### get\_config\_root

```python
@dispatch
def get_config_root(_: FindLocal) -> Optional[Path]
```

Try the path `$PWD/config` as root config folder

<a id="gamma.config.findconfig.get_config_root"></a>

#### get\_config\_root

```python
@dispatch
def get_config_root(_: FindJupyter) -> Optional[Path]
```

Try `<parent>/config` folders iteratively if we're in a Jupyter (IPython)
environment

<a id="gamma.config.findconfig.load_dotenv"></a>

#### load\_dotenv

```python
def load_dotenv(root: Path = None)
```

Load dotenv files located in:

- `$PWD/config.local.env`
- `{config_root}/../config.local.env`
- `$PWD/config.env`
- `{config_root}/../config.env`

<a id="gamma.config.render_context"></a>

# gamma.config.render\_context

Module handling rendering context variables (eg. for !expr and !j2)

<a id="gamma.config.render_context.ContextVar"></a>

## ContextVar Objects

```python
class ContextVar(NamedTuple)
```

A specification for a context variable used for rendering dynamic values.

Either if ``function`` is specified, we'll call the function to get the actual
value.

<a id="gamma.config.render_context.ContextVar.name"></a>

#### name

The name of the variable

<a id="gamma.config.render_context.ContextVar.value"></a>

#### value

The value of the variable

<a id="gamma.config.render_context.ContextVar.function"></a>

#### function

Function to call to resolve the variable

<a id="gamma.config.render_context.ContextVar.cacheable"></a>

#### cacheable

If True, will cache the function result, otherwise will call on each render.

<a id="gamma.config.render_context.get_render_context"></a>

#### get\_render\_context

```python
def get_render_context(**kwargs) -> Dict[str, Any]
```

Return the render context by calling each function in ``context_provider``.

A context provider must be a function with the signature:
    `(**kwargs) -> List[ContextVar]`
or simply a list of `ContextVar` objects

The provided `**kwargs` are the same available in the `render_node` function

<a id="gamma.config.render_context.base_provider"></a>

#### base\_provider

```python
def base_provider(**kwargs)
```

Defaults to context

- `env` -> os.environ
- `c` -> the global RootConfig

<a id="gamma.config.render_context.underscore_context_provider"></a>

#### underscore\_context\_provider

```python
def underscore_context_provider(*, config: ConfigNode = None, **kwargs)
```

Look in parent config nodes and add all entries under the `_context` key

<a id="gamma.config.render_context.context_providers"></a>

#### context\_providers

Provides a list of context providers. See :func:get_render_context() for details

<a id="gamma.config.globalconfig"></a>

# gamma.config.globalconfig

Module dealing with the lifecycle of the global `RootConfig` object

<a id="gamma.config.globalconfig._GlobalStore"></a>

## \_GlobalStore Objects

```python
class _GlobalStore()
```

Implements a global store holder object.

This store operates as a restricted version of a thread-local, where you can only
ovewrite the value in the same thread/processes where it was first set.

<a id="gamma.config.globalconfig._GlobalStore.set"></a>

#### set

```python
def set(root, force=False) -> None
```

Set the new root config.

To avoid unwanted suprises, by defaul we allow updating the global root config
only by the same thread that created it.

**Arguments**:

- `root` - the RootConfig to store
- `force` - if True, do not check for thread safety

<a id="gamma.config.globalconfig._GlobalStore.check_can_modify"></a>

#### check\_can\_modify

```python
def check_can_modify(key=None) -> None
```

Raises an Exception modifying the config would break the same thread rule.

**Arguments**:

- `key` - the key to check, fetches one if `None`

<a id="gamma.config.globalconfig.get_config"></a>

#### get\_config

```python
def get_config(initialize: bool = True) -> Optional[RootConfig]
```

Get the global config root object, loading if needed and `initialize` is `True`.

This global object is cached and safe to call multiple times, from multiple
threads.

<a id="gamma.config.globalconfig.reset_config"></a>

#### reset\_config

```python
def reset_config(force: bool = False) -> None
```

Clear the global store and cache.

This is not meant to be used extensively by applications, but can be useful for
writing tests.

**Arguments**:

- `force` - if True, will reset the global store regardless of the current
  thread/process.

<a id="gamma.config.globalconfig.set_config"></a>

#### set\_config

```python
def set_config(cfg: RootConfig) -> None
```

Forces a root config.

Call `reset_config`.

NOTE: This is not meant to be used regularly by applications, but can be useful
when writing tests.

<a id="gamma.config.globalconfig.check_can_modify"></a>

#### check\_can\_modify

```python
def check_can_modify(cfg: RootConfig) -> None
```

Check if this root config object can be modified.

As specified, the **global** root config object can only be modified by the thread
that first created it.

<a id="gamma.config.dump_yaml"></a>

# gamma.config.dump\_yaml

<a id="gamma.config.dump_yaml.to_yaml"></a>

#### to\_yaml

```python
@dispatch
def to_yaml(cfg: RootConfig, resolve_tags: bool)
```

Dump a config/node to the YAML representation.

**Arguments**:

- `resolve_tags` - if True, will render tags, otherwise, dump tags unrendered.

<a id="gamma.config.dump_yaml.to_yaml"></a>

#### to\_yaml

```python
@dispatch
def to_yaml(cfg: ConfigNode)
```

Render a ConfigNode assuming default of `resolve_tags` = True

<a id="gamma.config.dump_yaml.dump_node"></a>

#### dump\_node

```python
@dispatch
def dump_node(node: ScalarNode, *, config=None)
```

Dump a `scalar` node as raw YAML node

<a id="gamma.config.dump_yaml.dump_node"></a>

#### dump\_node

```python
@dispatch
def dump_node(node: SequenceNode, *, config=None)
```

Dump a `seq` node as raw YAML node

<a id="gamma.config.dump_yaml.dump_node"></a>

#### dump\_node

```python
@dispatch
def dump_node(node: MappingNode, *, config=None)
```

Dump a `scalar` node as raw YAML node

<a id="gamma.config.dump_dict"></a>

# gamma.config.dump\_dict

<a id="gamma.config.dump_dict.to_dict"></a>

#### to\_dict

```python
@dispatch
def to_dict(node, **ctx)
```

Converts a node to a dictionary.

<a id="gamma.config.dump_dict.to_dict"></a>

#### to\_dict

```python
@dispatch
def to_dict(node: ConfigNode, **ctx)
```

Converts a ConfigNode to a dictionary.

<a id="gamma.config.dump_dict.to_dict"></a>

#### to\_dict

```python
@dispatch
def to_dict(node: MappingNode, **ctx)
```

Render MappingNodes as dict regardless of tag value

<a id="gamma.config.dump_dict.to_dict"></a>

#### to\_dict

```python
@dispatch
def to_dict(node: SequenceNode, **ctx)
```

Render SequenceNodes as list regardless of tag value

<a id="gamma.config.scaffold"></a>

# gamma.config.scaffold

Module to 'scaffold' append bootstrap config for gamma-io

<a id="gamma.config.scaffold.scaffold"></a>

#### scaffold

```python
def scaffold(target, force)
```

Initialize the config folder with samples.

The set of files to be deployed on scaffolding can be extended via the Python
"entrypoint" plugin system.

First you need to add your the directives in `setup.cfg` pointing to the
`gamma.config.scaffold` group. Example:


In the example above, `setup` function under `gamma.io.scaffold` module should
return an instance of any class that will be used for dispatching the `get_files`
and `get_source` functions.
```ini
[options.entry_points]
gamma.config.scaffold =
    gamma-io = gamma.io.scaffold:setup
```

<a id="gamma.config.merge"></a>

# gamma.config.merge

Implements the node merging functionality

<a id="gamma.config.merge.merge_nodes"></a>

#### merge\_nodes

```python
@dispatch
def merge_nodes(nodes: List)
```

Merge nodes iterable, ignoring key

<a id="gamma.config.merge.merge_nodes"></a>

#### merge\_nodes

```python
@dispatch
def merge_nodes(l_node: MappingNode, r_node: MappingNode)
```

Merge map nodes ignoring key

<a id="gamma.config.merge.merge_nodes"></a>

#### merge\_nodes

```python
@dispatch
def merge_nodes(left: Tuple, r_node: MappingNode)
```

Merge map nodes ignoring key (for assymetric fold-left)

<a id="gamma.config.merge.merge_nodes"></a>

#### merge\_nodes

```python
@dispatch
def merge_nodes(left: Tuple, right: Tuple)
```

Merge map nodes (symetric fold-left)

**Arguments**:

  left, right: Tuple of (key: Node, value: Node)

<a id="gamma.config.merge.merge_nodes"></a>

#### merge\_nodes

```python
@dispatch
def merge_nodes(l_key, l_node: Union[None, Node], r_key, r_node: Union[None, Node])
```

Merge scalars.

Return "right", or "left" if "right" is `None`

<a id="gamma.config.merge.merge_nodes"></a>

#### merge\_nodes

```python
@dispatch
def merge_nodes(l_key, l_node: MappingNode, r_key, r_node: MappingNode)
```

Merge `map` nodes recursively.

Right side has precedence. `@hint: merge_replace` overrides merging, returning
right.

<a id="gamma.config.merge.merge_nodes"></a>

#### merge\_nodes

```python
@dispatch
def merge_nodes(l_key, l_node: SequenceNode, r_key, r_node: SequenceNode)
```

Merge `sequence` nodes recursively.

Right side has precedence. `@hint: merge_replace` overrides merging, returning
right.

<a id="gamma.config.merge.has_replace_hint"></a>

#### has\_replace\_hint

```python
@dispatch
def has_replace_hint(node: Node) -> bool
```

Check for existence of config "hint" in the node's comments.

Only `@hint: merge_replace` is supported.

<a id="gamma.config.builtin_tags"></a>

# gamma.config.builtin\_tags

Module that implements renderers for builtin-tags

<a id="gamma.config.builtin_tags.render_node"></a>

#### render\_node

```python
@dispatch
def render_node(node: Node, tag: EnvTag, **ctx) -> str
```

[!env] Maps the value to an environment variable of the same name.

You can provide a default using the ``|`` (pipe) character after the variable
name.

**Examples**:

  
- `my_var` - !env MYVAR|my_default

<a id="gamma.config.builtin_tags.render_node"></a>

#### render\_node

```python
@dispatch
def render_node(node: Node, tag: EnvSecretTag, *, dump=False, **ctx) -> str
```

[!env_secret] Similar to !env, but never returns the value when dumping.

<a id="gamma.config.builtin_tags.render_node"></a>

#### render\_node

```python
@dispatch
def render_node(node: Node, tag: ExprTag, **ctx) -> Any
```

[!expr] Uses ``eval()`` to render arbitrary Python expressions.

By default, we add the root configuration as `c` variable.

See ``gamma.config.render_context.context_providers`` documentation to add your
own variables to the context.

<a id="gamma.config.builtin_tags.render_node"></a>

#### render\_node

```python
@dispatch
def render_node(node: Node, tag: J2Tag, *, config=None, key=None, **ctx) -> Any
```

[!j2] Treats the value a Jinj2 Template

See ``gamma.config.render_context.context_providers`` documentation to add your
own variables to the context.

In practice, in the snippet bellow, ``foo1`` and ``foo2`` are equivalent

myvar: 100
foo1: !expr f"This is a number = {c.myvar}"
foo2: !j2 This is a number = {c.myvar}

You can customize the Jinja2 environment by providing a reference to a Python
function in the `j2_env` key in `00-meta.yaml`. Example

j2_env: my_app.my_module:my_func

**Notes**:

  * Jinja2 is not installed by default, you should install it manually.

<a id="gamma.config.builtin_tags.render_node"></a>

#### render\_node

```python
@dispatch
def render_node(node: Node, tag: J2SecretTag, *, dump=False, **ctx) -> Any
```

[!j2_secret] Similar to !j2, but never returns the value when dumping.

<a id="gamma.config.builtin_tags.render_node"></a>

#### render\_node

```python
@dispatch
def render_node(node: Node, tag: RefTag, *, config=None, recursive=False, **ctx) -> Any
```

[!ref] References other entries in the config object.

Navigate the object using the dot notation. Complex named keys can be accessed
using quotes.

<a id="gamma.config.builtin_tags.render_node"></a>

#### render\_node

```python
@dispatch
def render_node(node: ScalarNode, tag: PyTag, *, path=None, **ctx) -> Any
```

[!py] Pass the node value to a Python callable.

This tag should be used as a URI-style tag on the form `!py:<module>:<callable>`

The scalar node value is first implicitly resolved to a Python object using
`yaml.load`. For instance:

```yaml
foo: !py:myapp.mymodule:myfunc 100
bar: !py:myapp.mymodule:myfunc "100"
zig: !py:myapp.mymodule:myfunc a value
```

Will call the function `myfunc` in `myapp.mymodule` module with the arguments:
- `type(value) == int; value == 100` for `foo`
- `type(value) == str; value == "100"` for `bar`
- `type(value) == str; value == "a value"` for `zig`

<a id="gamma.config.builtin_tags.render_node"></a>

#### render\_node

```python
@dispatch
def render_node(node: Union[SequenceNode, MappingNode], tag: PyTag, *, path=None, **ctx) -> Any
```

[!py] Pass the node value to a Python callable.

This tag should be used as a URI-style tag on the form `!py:<module>:<callable>`

The `map` or `seq` node value is first converted to a Python `dict`/`list`
recursively using the `to_dict` method.

<a id="gamma.config.builtin_tags.render_node"></a>

#### render\_node

```python
@dispatch
def render_node(node: MappingNode, tag: ObjTag, *, path=None, config=None, **ctx) -> Any
```

[!obj] Create a Python object by passing the mapping value as nested dicts to
the object constructor.

This tag should be used as a URI-style tag on the form `!obj:<module>:<callable>`
It behaves like `!py`, but only applies to `map` nodes, and
automatically unpack the mapping.

You may omit the `<module>` part of the path if you define an `obj_default_module`
scalar entry at the root of the config.

**Examples**:

  
```yaml
foo: !obj:myapp.mymodule:MyClass
    a: 100
    b: a value

# the above `foo` is equivalent to `bar` below

obj_default_module: myapp.mymodule

bar: !obj:MyClass
    a: 100
    b: a value
```

<a id="gamma.config.builtin_tags.render_node"></a>

#### render\_node

```python
@dispatch
def render_node(node: Node, tag: PathTag, **ctx) -> str
```

[!path] Construct an absolute file path by joining a path
fragment to the known path of the *parent* of config root directory

**Examples**:

  # should point to `<config-root>/../data/hello_world.csv`
- `my_var` - !path data/hello_world.csv

<a id="gamma.config.rawnodes"></a>

# gamma.config.rawnodes

Module implementing convenience methods for dealing with `ruamel.yaml` `Node`s

<a id="gamma.config.rawnodes.get_keys"></a>

#### get\_keys

```python
@dispatch
def get_keys(node: MappingNode) -> Iterable[Node]
```

Get all keys on a `map` node

<a id="gamma.config.rawnodes.get_item"></a>

#### get\_item

```python
@dispatch
def get_item(node: MappingNode, key, *, default=...) -> Node
```

Get a single child node item from `map` node

<a id="gamma.config.rawnodes.get_entry"></a>

#### get\_entry

```python
@dispatch
def get_entry(node: MappingNode, key, *, default=...) -> Entry
```

Get a (key, value) entry from a `map` node.

**Arguments**:

- `default` - return this value instead of `KeyError` if not found.
  
  Raise:
  `KeyError` if key not found and `default` not provided

<a id="gamma.config.rawnodes.is_equal"></a>

#### is\_equal

```python
@dispatch
def is_equal(a: ScalarNode, b) -> bool
```

Check if `a` is equal to `b`

<a id="gamma.config.rawnodes.is_equal"></a>

#### is\_equal

```python
@dispatch
def is_equal(a, b: ScalarNode) -> bool
```

Check if `a` is equal to `b`

<a id="gamma.config.rawnodes.as_node"></a>

#### as\_node

```python
@dispatch
def as_node(a) -> Node
```

Return the `Node` representation of a given object.

This method handle basic scalar types.

<a id="gamma.config.rawnodes.get_id"></a>

#### get\_id

```python
@dispatch
def get_id(a: ScalarNode) -> Hashable
```

Return an object that allows to ScalarNodes to be hashed and compared

<a id="gamma.config.rawnodes.is_in"></a>

#### is\_in

```python
@dispatch
def is_in(node: Node, container: Iterable[Any]) -> bool
```

Return true if `node` is in `container`

<a id="gamma.config.rawnodes.get_entries"></a>

#### get\_entries

```python
@dispatch
def get_entries(node: MappingNode) -> Iterable[Entry]
```

Return all entries (key, value) in this `map` node

<a id="gamma.config.rawnodes.get_values"></a>

#### get\_values

```python
@dispatch
def get_values(node: SequenceNode) -> Iterable[Node]
```

Return all values in this `seq` node

<a id="gamma.config.rawnodes.get_values"></a>

#### get\_values

```python
@dispatch
def get_values(node: MappingNode) -> Iterable[Node]
```

Return all values in this `map` node

<a id="gamma.config.rawnodes.union_nodes"></a>

#### union\_nodes

```python
@dispatch
def union_nodes(first: Iterable, second: Iterable) -> Iterable
```

Union two sets of nodes.

By default we keep the ones in `first` if equals.

<a id="gamma.dispatch"></a>

# gamma.dispatch

<a id="gamma.dispatch.dispatchsystem"></a>

# gamma.dispatch.dispatchsystem

<a id="gamma.dispatch.dispatchsystem.methods_matching"></a>

#### methods\_matching

```python
def methods_matching(call, table) -> List
```

Given a method table, return the methods matching the call signature.

**Arguments**:

- `table` - an iterable of methods ordered by `is_more_specific`
- `call` - the call signature as a `Sig` object or `Tuple[...]` type

<a id="gamma.dispatch.dispatchsystem.dispatch"></a>

## dispatch Objects

```python
class dispatch()
```

Function wrapper to dispatch methods.

**Arguments**:

- `namespace` - If set, use a shared namespace with `namespace` as key, otherwise
  try to find matching functions in `locals`.
- `specialize` - If set, will throw an error if this function is not a specialization
  of an already existing function.
- `overwrite` - When `True`, won't issue a warning about overwriting a method.

<a id="gamma.dispatch.dispatchsystem.dispatch.pending"></a>

#### pending

Pending methods register due to forward references

<a id="gamma.dispatch.dispatchsystem.dispatch.methods"></a>

#### methods

The methods table for this function

<a id="gamma.dispatch.dispatchsystem.dispatch.cache"></a>

#### cache

Cache from call signature to actual function

<a id="gamma.dispatch.dispatchsystem.dispatch.get_type"></a>

#### get\_type

Callable to get types from function arguments

<a id="gamma.dispatch.dispatchsystem.dispatch.name"></a>

#### name

function name

<a id="gamma.dispatch.dispatchsystem.dispatch.arg_names"></a>

#### arg\_names

set of reserved argument names

<a id="gamma.dispatch.dispatchsystem.dispatch.register"></a>

#### register

```python
def register(func: Callable, *, overwrite=False, allow_pending=True) -> Callable
```

Register a new method to this function's dispatch table.

**Arguments**:

- `func` - the method to register
- `overwrite` - if False, will warn if the registration will overwrite and
  existing registration.
- `allow_pending` - if True, won't error on forward references

<a id="gamma.dispatch.dispatchsystem.dispatch.clear"></a>

#### clear

```python
def clear()
```

Empty the cache.

<a id="gamma.dispatch.dispatchsystem.dispatch.__setitem__"></a>

#### \_\_setitem\_\_

```python
def __setitem__(key, func: Callable)
```

Manually map a call signature to a callable

<a id="gamma.dispatch.dispatchsystem.dispatch.__delitem__"></a>

#### \_\_delitem\_\_

```python
def __delitem__(types: Tuple)
```

Remove a method registration

<a id="gamma.dispatch.dispatchsystem.dispatch.find_method"></a>

#### find\_method

```python
def find_method(key: Tuple) -> Callable
```

Find and cache the next applicable method of given types.

**Arguments**:

- `key` - A call args types tuple.

<a id="gamma.dispatch.dispatchsystem.dispatch.__call__"></a>

#### \_\_call\_\_

```python
def __call__(*args, **kwargs)
```

Resolve and dispatch to best method.

<a id="gamma.dispatch.dispatchsystem.dispatch.resolve_pending"></a>

#### resolve\_pending

```python
def resolve_pending()
```

Evaluate any pending forward references.

This can be called explicitly when using forward references,
otherwise cache misses will evaluate.

<a id="gamma.dispatch.dispatchsystem.dispatch.dump"></a>

#### dump

```python
def dump() -> str
```

Pretty-print debug information about this function

<a id="gamma.dispatch.typesystem"></a>

# gamma.dispatch.typesystem

Module implementing core rules in Julia's dispatch system. For reference,
check Jeff Bezanson's PhD thesis at
https://github.com/JeffBezanson/phdthesis/blob/master/main.pdf

<a id="gamma.dispatch.typesystem.Sig"></a>

## Sig Objects

```python
class Sig()
```

Represent a Tuple type with extra features, mostly used for method signature
dispatching

<a id="gamma.dispatch.typesystem.pad_varargs"></a>

#### pad\_varargs

```python
def pad_varargs(a, b) -> Tuple[Tuple[Type], Tuple[Type]]
```

Extract Tuple args and pad with `object`, accounting for varargs

<a id="gamma.dispatch.typesystem.issubtype"></a>

#### issubtype

```python
def issubtype(_type: Union[Type, Sig], _super: Union[Type, Sig])
```

Check if `_type` is a subtype of `_super`.

Arguments are either `Type` (including parameterized Type) or `Sig` (signature).

Follow rules in 4.2.2 in Bezanson's thesis.

Generic (aka parametric) types are invariant. For instance:
    `issubtype(List[int], List[object]) == False`
    `issubtype(List[int], List[int]) == True`
    `issubtype(list, List[object]) == False`

The exceptions are:
    * `Tuple`: these are covariant. Eg:
        - `issubtype(Tuple[Foo], Tuple[Super]) == True` where `Foo -> Super`

    * `Union`: match if there's a covariant intersection, including non-union types
        - `issubtype(Foo, Union[str, Super]) == True` where `Foo -> Super`
        - `issubtype(str, Union[str, Super]) == True`

    * `typing.Type`: is covariant on the type argument. `type` is treated as
      `typing.Type[object]`
        - `issubtype(typing.Type[str], typing.Type[object]) == True`
        - `issubtype(typing.Type[str], type) == True`

Since Python don't tag container instances with the type paramemeters
(eg. `type([1,2,3]) == list`) this means that we can't dispatch lists as we would
with arrays in Julia. The multiple dispatch system must then erase method signature
generic information for such container types.

See the `parametric` module for a way to declare and dispatch on parametric types.

Also, we don't currently support the equivalent of `UnionAll`. This is not an issue
since we don't support parametric dispatch, ie. `TypeVar`s in method signatures.

<a id="gamma.dispatch.typesystem.signatures_from"></a>

#### signatures\_from

```python
def signatures_from(func: Callable) -> Iterable[Sig]
```

Parse a callable to extract the dispatchable type tuple.

<a id="gamma.dispatch.poset"></a>

# gamma.dispatch.poset

<a id="gamma.dispatch.poset.PODict"></a>

## PODict Objects

```python
class PODict(MutableMapping,  Generic[KT, VT])
```

Dictionary that stores keys sorted (like a prio queue) that works
for partial orders

<a id="gamma.dispatch.parametric_types"></a>

# gamma.dispatch.parametric\_types

<a id="gamma.dispatch.parametric_types.parametric"></a>

## parametric Objects

```python
class parametric(Generic[T])
```

Decorator to create new parametric base classes

<a id="gamma.dispatch.parametric_types.ValMeta"></a>

## ValMeta Objects

```python
class ValMeta(ParametricMeta)
```

<a id="gamma.dispatch.parametric_types.ValMeta.values"></a>

#### values

```python
@property
def values(cls) -> Tuple
```

Return all values used to create the parametric value type

<a id="gamma.dispatch.parametric_types.Val"></a>

## Val Objects

```python
class Val(, metaclass=ValMeta)
```

Generic parametric class with easy value accessors

