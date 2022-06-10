## Writing custom tags

We use [multiple dispatch](https://en.wikipedia.org/wiki/Multiple_dispatch) for almost everything in `gamma.config`, including which function to call when we need to render a node in the parsed YAML tree. Adding your own tag handler requires just adding the function to the `dispatch` table like in the example below:

```py
import os
from gamma.dispatch import dispatch                             # (1)
from gamma.config import ScalarNode, Tag, render_node           # (2) (3)

MyEnvTag = Tag["!myenv"]                                        # (4)

@dispatch
def render_node(node: ScalarNode, tag: MyEnvTag, **ctx):        # (5)
    """Simpler clone of !env"""
    return os.getenv(node.value)                                # (6)
```

In more details:

1. We import `gamma.dispatch.dispatch`, that register our function as a dispatchable function.

2. We import `gamma.config.render_node`, to indicate we want to add another function to the dispatch table. A **very common mistake** is to forget to import the function, thus creating a _new_ dispatchable function instead of extending the existing one.

3. We import `ScalaNode` and `Tag` types that we'll use to _specialize_ the `render_node` function.

4. Because we want to dispatch on a **specific** tag, we create a specialized `MyEnvTag` type from the general `Tag` type using a **parameter**. We call these _parametric_ or _value_ types.

5. We annotate our function with the specific types. The order of the arguments matter! The dispatch mechanics ignore keyword-only or untyped arguments.

6. Whatever we return will be the value returned when accessing the configuration.

And that's it! You just need to ensure the code is loaded before rendering
the config value.

### Render node arguments

The `node` argument comes directly from [ruaml.yaml](https://sourceforge.net/p/ruamel-yaml/code/ci/default/tree/nodes.py#l12) package. For `ScalarNode`s usually you're interested in the `node.value`, that provides the exact string in the YAML file.

If you want to use the standard YAML inference from `ruamel.yaml` package, you can do as follows:

```py
# ... other imports as above ...
from gamma.config import yaml
# ...

@dispatch
def render_node(node: ScalarNode, tag: MyEnvTag, **ctx):
    """Simpler clone of !env"""
    val = os.getenv(node.value)
    return yaml.load(val)  # parse the string into YAML core scalar types (str, int,
                           # float, bool, timestamp, null)
```

For `MappingNode` or `SequenceNode`, the `node.value` object is more complex. To avoid having to write your own recursive parsing logic, you can use the `to_dict` dump function to get a rendered object, including child nodes. (yes, it works with `Sequence`s as well)

```py
# ... other imports as above ...
from gamma.config import to_dict
# ...

@dispatch
def render_node(node: ScalarNode, tag: MyObjTag, **ctx):
    """Simply return the dict/list value of the node"""
    val = to_dict(node)
    return val      # parse node recursively, handing children as needed
```

The `ctx` kwargs dict allows you to access contextual information when rendering and **may** contain the following entries:

-   `key`: The node key, also as a ruamel YAML node.
-   `config`: The current ConfigNode object.
-   `dump`: Flag indicating we're dumping the data to a potentially insecure
    destination, so sensitive data should not be returned.
-   `path`: The URI path for URI-style tag dispatch _(see below)_.

### URI-style tags

The default tag dispatch mechanism is to dispatch on the resolved tag value using a parameterized `Tag` subtype. For instance, `foo: !mytag 1` will only dipatch on `(node: ScalarNode, tag: Tag["!mytag"])`.

However, if the tag contains a `:` (colon), we're assuming the tag is an _URI-style tag_ of the format (`![scheme]:[path]`). Besides the default tag dispatch, URI-style tags will also dispatch on the _scheme_ part only, and pass a `path` keywork arg to the `render_node` function.

An example:

```yaml
foo: !mytag:mypath 1
```

will dispatch first on `(node: ScalarNode, tag: Tag["!mytag:mypath"])` and, failing to find such method, will also try `(node: ScalarNode, tag: Tag["!mytag"])` with `path = "mypath"` as extra keyword argument.

## Extending the render context

Some tags like `!j2` and `!expr` allow you to refer to variables in the _render context_.
By default, we provide `env` and `c`, refering to a dict of environment variables, and
to the root config itself.

We also allow you to add a `_context` mapping entry to any parent node to extend the
render context without needing to write any code. This is useful to provide contextual
parameters in a concise way in some scenarios. Example:

```yaml

catalog:
  _context:
    inputs: s3://mybucket/myproject/inputs

  datasets:
    customers: !j2 "{{ inputs }}/customers"   # will reference the context above
```

If you need to extend the render context, please refer to docstrings in the source file
`gamma/config/render_context.py` [APIDocs here](/api?id=gammaconfigrender_context)
