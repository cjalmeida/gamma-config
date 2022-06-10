# Built-in tags

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
-   Anything under a `_context` map in a parent node

In practice, in the snippet bellow:

```yaml
myvar: 100
foo1: !j2 Number = {{ c.myvar }}
level0:
  _context:
    custom_var: myvalue

  bar1: !j2 Custom = {{ custom_var }}
```

The value of `foo1` is the string `Number = 100`. The value of `level0.bar1` is `Custom = myvalue` because we defined `_context` in a parent node. See the section on [extending the render context](tags?id=extending-the-render-context) to add your own variables.

We also provide `!j2_secret` to be used when dealing with sensitive data

!!! note 
    Jinja2 **is not installed by default**, you should install yourself by
    running `pip install jinja2` or, more generally adding the `jinja2` extra package
    dependency.

### !ref

References another entry in the config object, even if it's in another file or
overriden by an environment specific entry. If you key has a `.` (dot) or other
special characters, you can wrap the key in single-quotes `'`.

Example:

```yaml
key_a:
    sub_key: 100

key_b:
    "my sub": bar

# use dot notation to access nested entries
# will be the same as key_a -> subkey == 100
ref_a: !ref key_a.sub_key
ref_b: !ref key_b.'my sub'
```

### !expr

Allows you to evalute arbitrary Python expressions, using the `eval()` built-in. The default variables available are:

-   `env`: a dict of the system environment variables
-   `c`: a reference to the root config object
-   Anything under a `_context` map in a parent node

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

!!! tip
    This tag is particularly useful when integrating with validation libraries.
    [Pydantic](https://pydantic-docs.helpmanual.io/) in particular supports parsing
    nested `dict`s into an object tree. See [structured configuration](/structured).

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

### !path

Return an absolute path string, relative to the **parent of the config root folder**.

For example, consider you have a `data` folder located as a sibling to
`config` and want to reference a file in it:

```yaml
my_var: !path data/hello_world.csv
```

