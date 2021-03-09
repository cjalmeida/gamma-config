# Built-in and custom tags

In `gamma-config`, YAML tags provide dynamic behavior to the configuration allowing the resulting config object to centralize all application parameters. While we provide a good set of built-in tags, you're encouraged to write custom tags to fit your
application needs.

## Built-in tags reference

### !env

References a system environment variable. **Do not use this tag to load secrets** as
the contents are dumped by default on the `to_yaml()` call. You can use the `|`
(pipe) character to provide a default if a value is missing.

Example:

```yaml
sample_key:
    my_var: !env VAR|my_default
```

### !env_secret

Similar to `!env` but won't dump the variable contents.

Example:

```yaml
sample_key:
    my_var: !env_secret SECRET|my_secret
```

### !j2 or !j2_secret

Allow the use of Jinja2 templates. The default variables available are:

-   `env`: a dict of the system environment variables
-   `c`: a reference to the root config object

In practice, in the snippet bellow:

```yaml
myvar: 100
foo1: !j2 Number = {c.myvar}
```

The value of `foo1` is the string `Number = 100`. See the section on [extending the render context](tags?id=extending-the-render-context) to add your own variables.

We also provide `!j2_secret` to be used when dealing with sensitive data


!> Jinja2 **is not installed by default**, you should install yourself by
running `pip install jinja2` or, more generally adding the `jinja2` extra package
dependency.

### !ref

References another entry in the config object, even if it's in another file or
overriden by an environment specific entry.

Example:

```yaml
key_a:
    sub_key: 100

# use dot notation to access nested entries
# will be the same as key_a -> subkey == 100
key_b: !ref key_a.sub_key
```

### !expr

Allows you to evalute arbitrary Python expressions, using the `eval()` built-in. The default variables available are:

-   `env`: a dict of the system environment variables
-   `c`: a reference to the root config object

Example usage:

```yaml
sample_key:
    # we may need to enclose the whole expression in quotes to keep it valid YAML
    my_var: !expr '"This is an env variable" + env["USER"]'
```

See the section on [extending the render context](tags?id=extending-the-render-context) to add your own variables.

### !py

##### Usage: `!py:[module]:[callable]`

Wraps the rendered node by calling a Python callable (class, function, etc.)

> [!TIP]
> This tag is an example of a [URI style tags](tags?id=uri-style-tags).

Example usage:

```py
# in module myapp.foo
def split_dict(val)
    return val["a"], val["b"]
```

and config:

```yaml
# here we're looking for callable `split_dict` in module `myapp.foo`
foo: !py:myapp.foo:split_dict
    a: 1
    b: 2
```

The following holds:

```py
    config = get_config()
    a, b = config["foo"]
    assert a == 1 and b == 2
```

### !obj

##### Usage: `!obj:[module]:[callable]` or `!obj:[callable]`

Specialized version of the `!py` tag above, designed to pass dictionaries as expanded `**kwargs` of the callable. It also allows you to define a default module by adding
a `obj_default_module` entry in the root of the config file.

Unlike the `!py` tag, it only support mapping nodes.

> [!TIP]
> This tag is particularly useful when integrating with validation libraries.
> [Pydantic](https://pydantic-docs.helpmanual.io/) in particular supports parsing
> nested `dict`s into an object tree.

Example usage:

```py
# in module myapp.config
@dataclass
class Section:
    a: int
    b: int
```

and config

```yaml
obj_default_module: myapp.config

foo: !obj:Section
    a: 1
    b: 2
```

The following holds:

```py
    config = get_config()
    section = config["foo"]
    assert section.a == 1 and section.b == 2
```

## Writing custom tags

We use [multiple dispatch](https://en.wikipedia.org/wiki/Multiple_dispatch) for almost everything in `gamma.config`, including which function to call when we need to render a node in the parse YAML tree. Adding your own tag handler requires just adding the function to the `dispatch` table like in the example below:

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

## Customize the render context variables

Some tags like `!j2` and `!expr` allow you to refer to variables in the *render context*.
By default, we provide `env` and `c`, refering to a dict of environment variables, and
to the root config itself.

If you need to extend the render context, please refer to docstrings in the source file
`gamma/config/render_context.py` [APIDocs here](/api?id=gammaconfigrender_context)
