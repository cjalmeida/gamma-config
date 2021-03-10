<a name="gamma.config"></a>
# gamma.config

<a name="gamma.config.confignode"></a>
# gamma.config.confignode

<a name="gamma.config.confignode.RootConfig"></a>
## RootConfig Objects

```python
class RootConfig(ConfigNode)
```

<a name="gamma.config.confignode.RootConfig.__init__"></a>
#### \_\_init\_\_

```python
 | __init__(entry_key: Optional[str] = None, entry=None) -> None
```

Initialize the root config with optionally a default entry

New entries should be inserted with the ``push_entry`` function.
The entries are always iterated in ``entry_key`` lexicographical
sort order and this affects merge results.

<a name="gamma.config.confignode.push_entry"></a>
#### push\_entry

```python
@dispatch
push_entry(root: RootConfig, entry_key: str, entry, content_type=None) -> None
```

Add an entry to the root config.

The entry itself can be of any supported format by ``load_node``. You can
disambiguate between string/bytes values by providing an optional ``content_type``

<a name="gamma.config.tags"></a>
# gamma.config.tags

<a name="gamma.config.cache"></a>
# gamma.config.cache

<a name="gamma.config.load"></a>
# gamma.config.load

<a name="gamma.config.load.load_node"></a>
#### load\_node

```python
@dispatch
load_node(stream: IOBase, content_type=None) -> Node
```

Load YAML data

<a name="gamma.config.render"></a>
# gamma.config.render

<a name="gamma.config.render.render_node"></a>
#### render\_node

```python
@dispatch
render_node(node: Node, tag: tags.Tag, *, key: Optional[Node] = None, config: "ConfigNode" = None, dump: bool = False, path: Optional[str] = None)
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
- `path` - The URI path for URI fallback dispatch


**Returns**:

  any value

<a name="gamma.config.render.render_node"></a>
#### render\_node

```python
@dispatch
render_node(node: SequenceNode, tag: tags.Seq, **args)
```

Render seq nodes

<a name="gamma.config.render.render_node"></a>
#### render\_node

```python
@dispatch
render_node(node: MappingNode, tag: tags.Map, **args)
```

Render map nodes

<a name="gamma.config.render.render_node"></a>
#### render\_node

```python
@dispatch
render_node(cfg: "RootConfig")
```

Render the resulting node of merging all entries

<a name="gamma.config.render.render_node"></a>
#### render\_node

```python
@dispatch
render_node(cfg: "ConfigNode", dump=True)
```

Render the config node. Defaults to "dump mode"!

**Arguments**:

- `dump` - If true, assume it's "dump mode" where secrets are not to be rendered.

<a name="gamma.config.findconfig"></a>
# gamma.config.findconfig

<a name="gamma.config.findconfig.get_config_root"></a>
#### get\_config\_root

```python
@dispatch
get_config_root() -> Path
```

Return the location for config root path.

The mechanisms used to find the config root are set in the ``CONFIG_LOAD_ORDER``
module variable.

<a name="gamma.config.findconfig.load_dotenv"></a>
#### load\_dotenv

```python
load_dotenv(root: Path = None)
```

Load dotenv files located in:

$PWD/config.local.env
{config_root}/../config.local.env
$PWD/config.env
{config_root}/../config.env

<a name="gamma.config.render_context"></a>
# gamma.config.render\_context

<a name="gamma.config.render_context.ContextVar"></a>
## ContextVar Objects

```python
class ContextVar(NamedTuple)
```

A specification for a context variable used for rendering dynamic values.

Either if ``function`` is specified, we'll call the function to get the actual
value.

<a name="gamma.config.render_context.ContextVar.name"></a>
#### name

The name of the variable

<a name="gamma.config.render_context.ContextVar.value"></a>
#### value

The value of the variable

<a name="gamma.config.render_context.ContextVar.function"></a>
#### function

Function to call to resolve the variable

<a name="gamma.config.render_context.ContextVar.cacheable"></a>
#### cacheable

If True, will cache the function result, otherwise will call on each render.

<a name="gamma.config.render_context.default_context_provider"></a>
#### default\_context\_provider

```python
default_context_provider()
```

Render context some defaults.

- `env` -> os.environ
- `c` -> the global RootConfig

<a name="gamma.config.render_context.context_providers"></a>
#### context\_providers

Provides a list of context providers. You can add your own if needed by appending
a function with the signature `() -> List[ContextVar]` or adding a list of
`ContextVar` objects

<a name="gamma.config.render_context.get_render_context"></a>
#### get\_render\_context

```python
get_render_context() -> Dict[str, Any]
```

Return the render context by calling each function in ``context_provider``.

A context provider must be a function with the signature:
    () -> List[ContextVar]
or simply a list of [ContextVar] objects

<a name="gamma.config.globalconfig"></a>
# gamma.config.globalconfig

<a name="gamma.config.globalconfig._GlobalStore"></a>
## \_GlobalStore Objects

```python
class _GlobalStore()
```

<a name="gamma.config.globalconfig._GlobalStore.set"></a>
#### set

```python
 | set(root, force=False)
```

Set the new root config.

To avoid unwanted suprises, by defaul we allow updating the global root config
only by the same thread that created it.

**Arguments**:

- `root` - the RootConfig to store
- `force` - if True, do not check for thread safety

<a name="gamma.config.dump_yaml"></a>
# gamma.config.dump\_yaml

<a name="gamma.config.dump_yaml.to_yaml"></a>
#### to\_yaml

```python
@dispatch
to_yaml(cfg: RootConfig, *, resolve_tags=False)
```

Dump a config/node to the YAML representation.

**Arguments**:

- `resolve_tags` - if True, will render tags, otherwise, dump tags unrendered.

<a name="gamma.config.dump_dict"></a>
# gamma.config.dump\_dict

<a name="gamma.config.dump_dict.to_dict"></a>
#### to\_dict

```python
@dispatch
to_dict(node)
```

Converts a node to a dictionary

<a name="gamma.config.dump_dict.to_dict"></a>
#### to\_dict

```python
@dispatch
to_dict(node: MappingNode)
```

Render MappingNodes as dict regardless of tag value

<a name="gamma.config.dump_dict.to_dict"></a>
#### to\_dict

```python
@dispatch
to_dict(node: SequenceNode)
```

Render SequenceNodes as list regardless of tag value

<a name="gamma.config.scaffold"></a>
# gamma.config.scaffold

<a name="gamma.config.scaffold.scaffold"></a>
#### scaffold

```python
scaffold(target, force)
```

Initialize the config folder with samples

<a name="gamma.config.merge"></a>
# gamma.config.merge

Implements the dictionary merging functionality

<a name="gamma.config.merge.merge_nodes"></a>
#### merge\_nodes

```python
@dispatch
merge_nodes(nodes: List)
```

Merge nodes iterable, ignoring key

<a name="gamma.config.merge.merge_nodes"></a>
#### merge\_nodes

```python
@dispatch
merge_nodes(l_node: MappingNode, r_node: MappingNode)
```

merge map nodes ignoring key

<a name="gamma.config.merge.merge_nodes"></a>
#### merge\_nodes

```python
@dispatch
merge_nodes(left: Tuple, r_node: MappingNode)
```

merge map nodes ignoring key (for assymetric fold-left)

<a name="gamma.config.merge.merge_nodes"></a>
#### merge\_nodes

```python
@dispatch
merge_nodes(left: Tuple, right: Tuple)
```

merge map nodes (symetric fold-left)

**Arguments**:

  left, right: Tuple of (key: Node, value: Node)

<a name="gamma.config.builtin_tags"></a>
# gamma.config.builtin\_tags

<a name="gamma.config.builtin_tags.render_node"></a>
#### render\_node

```python
@dispatch
render_node(node: Node, tag: EnvTag, **ctx) -> str
```

Maps the value to an environment variable of the same name.

You can provide a default using the ``|`` (pipe) character after the variable
name.

**Examples**:


- `my_var` - !env MYVAR|my_default

<a name="gamma.config.builtin_tags.render_node"></a>
#### render\_node

```python
@dispatch
render_node(node: Node, tag: EnvSecretTag, dump=False, **ctx) -> str
```

Similar to !env, but never returns the value when dumping.

<a name="gamma.config.builtin_tags.render_node"></a>
#### render\_node

```python
@dispatch
render_node(node: Node, tag: ExprTag, **ctx) -> Any
```

Uses ``eval()`` to render arbitrary Python expressions.

By default, we add the root configuration as `c` variable.

See ``gamma.config.render_context.context_providers`` documentation to add your
own variables to the context.

<a name="gamma.config.builtin_tags.render_node"></a>
#### render\_node

```python
@dispatch
render_node(node: Node, tag: J2Tag, **ctx) -> Any
```

Treats the value a Jinj2 Template

See ``gamma.config.render_context.context_providers`` documentation to add your
own variables to the context.

In practice, in the snippet bellow, ``foo1`` and ``foo2`` are equivalent

myvar: 100
foo1: !expr f"This is a number = {c.myvar}"
foo2: !j2 This is a number = {c.myvar}

**Notes**:

  * Jinja2 is not installed by default, you should install it manually.

<a name="gamma.config.builtin_tags.render_node"></a>
#### render\_node

```python
@dispatch
render_node(node: Node, tag: J2SecretTag, dump=False, **ctx) -> Any
```

Similar to !j2, but never returns the value when dumping.

<a name="gamma.config.builtin_tags.render_node"></a>
#### render\_node

```python
@dispatch
render_node(node: Node, tag: RefTag, config=None, **ctx) -> Any
```

References other entries in the config object.

Navigate the object using the dot notation. Complex named keys can be accessed
using quotes.

<a name="gamma.config.rawnodes"></a>
# gamma.config.rawnodes

<a name="gamma.config.rawnodes.get_id"></a>
#### get\_id

```python
@dispatch
get_id(a: ScalarNode)
```

Return an object that allows to ScalarNodes to be hashed and compared

<a name="gamma.config.rawnodes.union_nodes"></a>
#### union\_nodes

```python
@dispatch
union_nodes(first: Iterable, second: Iterable)
```

Union two sets of nodes.

By default we keep the ones in `first` if equals.

<a name="gamma.dispatch"></a>
# gamma.dispatch

<a name="gamma.dispatch.Val"></a>
## Val Objects

```python
@parametric
class Val()
```

Generic parametric class

