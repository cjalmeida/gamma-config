# Built-in tags

In `gamma-config`, YAML tags provide dynamic behavior to the configuration allowing the
resulting config object to centralize all application parameters. While we provide a
good set of built-in tags, you're encouraged to write custom tags to fit your
application needs.

## Built-in tags reference

### !env

!!! note "Changed in v0.8"

    The `!env` tag defaults to not dumping the contents when calling `to_yaml`.
    `!env_secret` is still supported but it's use is discouraged.

References a system environment variable. You can use the `|` (pipe) character to
provide a default if a value is missing. By default `!env` won't dump the content
when calling `to_yaml`, if you want to force this behavior, use `!env:dump`

Example:

```yaml
sample_key:
  my_var: !env VAR|my_default
```

### !j2

Allow the use of Jinja2 templates. The default variables available are:

- `env`: a dict of the system environment variables
- `c`: a reference to the root config object
- Anything under a `_context` map in a parent node. The `_context` map is searched
  and merged recursively until the root node.

In practice, in the snippet bellow:

```yaml
myvar: 100
foo1: !j2 Number = {{ c.myvar }}
level0:
  _context:
    custom_var: myvalue

  bar1: !j2 Custom = {{ custom_var }}
```

The value of `foo1` is the string `Number = 100`. The value of `level0.bar1` is `Custom = myvalue`
because we defined `_context` in a parent node. See the section on [extending
the render context](tags?id=extending-the-render-context) to add your own variables.

By default, `!j2` **will dump it's contents** when calling `to_yaml`. To avoid leaking
sensitive data please use `!j2:secret`.

!!! note

    Jinja2 **is not installed by default**, you should install yourself by
    running `pip install jinja2` or, more generally, adding the `jinja2` extra package
    dependency.

### !ref

References another entry in the config object, even if it's in another file or
overridden by an environment specific entry. If you key has a `.` (dot) or other
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

Allows you to evaluate arbitrary Python expressions, using the `eval()` built-in. The
default variables available are:

- `env`: a dict of the system environment variables
- `c`: a reference to the root config object
- Anything under a `_context` map in a parent node

Example usage:

```yaml
sample_key:
  # we may need to enclose the whole expression in quotes to keep it valid YAML
  my_var: !expr '"This is an env variable" + env["USER"]'
```

See the section on [extending the render context](tags?id=extending-the-render-context) to add your own variables.

By default `!expr` won't dump the content when calling `to_yaml`, if you want to force
this behavior, use `!expr:dump`

### !call

Allows you to call Python functions, including class constructors from the
configuration.

By default, the `!call` tag **will not** call the function when "dumping" the
configuration. If you want this behavior, you can force it by using `!call:dump`

---

**usage:** `!call <module>:<callable>(<args>)`

Similar to `!expr`, it will `eval()` the code replacing `<module>:<callable>` with the
right function reference.

Example usage:

```yaml
my_value: !call 'mypackage.subpackage:get_value("my-scope", "my-key")'
```

The value of `my_value` key is the result of calling `get_value("my-key", "custom-name")`
in the `mypackage.subpackage` module.

---

**usage:** `!call {func: <module>:<callable>, **<kwargs>}`

You can pass a mapping/dict to `!call`. It must contain either `_func` or `func` key
pointing the the callable, the rest of entries are passed as keyword arguments to
the callable.

Example usage:

```yaml
my_value: !call
  func: mypackage.subpackage:get_value
  scope: my-scope
  key: my-key
```

The value of `my_value` key is the result of calling `get_value(scope="my-key", key="custom-name")`
in the `mypackage.subpackage` module.

### !path

Return an absolute path string, relative to the **parent of the config root folder**.
This tag only works if you have only a single root folder defined.

For example, consider you have a `data` folder located as a sibling to
`config` and want to reference a file in it:

```yaml
my_var: !path data/hello_world.csv
```

### !py

!!! warning "Deprecation warning"

    The `!py` tag is scheduled for deprecation on release `1.0`, please use the cleaner
    `!call` tag.

**usage:** `!py:[module]:[callable]`

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

!!! warning "Deprecation warning"

    The `!obj` tag is scheduled for deprecation on release `1.0`, please use the cleaner
    `!call` tag.

**usage:** `!obj:[module]:[callable]` or `!obj:[callable]`

Specialized version of the `!py` tag above, designed to pass dictionaries as expanded `**kwargs` of the callable. It also allows you to define a default module by adding
a `obj_default_module` entry in the root of the config file.

Unlike the `!py` tag, it only support mapping nodes.

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
