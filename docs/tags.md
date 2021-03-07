# Built-in and custom tags

In `gamma.config`, YAML tags provide dynamic behavior to the configuration allowing the resulting config object to centralize all application parameters. While we provide a good set of built-in tags, you're encouraged to write custom tags to fit your
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

Allows you to evalute arbitrary Python expressions, using the `eval()` built-in. The
objects available in the expression evaluation context can extended using a plugin
hook implementation.

Example usage:

```yaml
sample_key:
    # we may need to enclose the whole expression in quotes to keep it valid YAML
    my_var: !expr '"This is an env variable" + env["USER"]'
```

In the example above, `env` is a render context variable pointing to `os.environ`. See the section on [extending the render context](tags?id=extending-the-render-context) to add your own variables.

### !py:[module]:[callable]

Wraps the rendered node by calling a Python callable (class, function, etc.)

>[!TIP]
>This tag is an example of a [URI style tags](tags?id=uri-style-tags).


Example usage:

```py
# in module myapp.foo
def split_dict(val)
    return val["a"], val["b"]
```

and config

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

### !obj:[module]:[callable] or !obj:[callable]

Specialized version of the `!py` tag above, designed to pass dictionaries as expandd `kwargs` of the callable. It also allows you to define a default module by adding
a `obj_default_module` entry in the root of the config file.

Unlike the `!py` tag, it only support mapping nodes.

>[!TIP]
>This tag is particularly useful when integrating with validation libraries such as
> [Pydantic](https://pydantic-docs.helpmanual.io/)


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

## Extending the render context
