# Using gamma-config in your app

Most of the time, using gamma-config should be as simple as calling `get_config()`
whenever you need to get a dict-like `config` object, like in the example below:

```python
from gamma.config import get_config

def do_something():

    config = get_config()
    assert config["foo"] == 1
    assert config.foo == 1
```

In the section below we'll discuss some patterns and caveats.

## Config object as a "default config"

If you try to access a non-existing value from the returned config object using the
dictionary style `config['missing']`, it will throw a `KeyError` as expected. However,
accessing using attribute style `config.missing` **will return an empty sub config**
object that (like regular dict) is *false-y*.


```python
config = get_config()

try:
    val = config["missing"] == 1          # this will throw KeyError
except KeyError:
    pass

val = config.missing                    # val is an empty ConfigNode object
assert not val                          # and is 'false-y` like empty dict
```

This behavior allows you to conveniently navigate deep across nodes, but can be
backfire. Stick to the dictionary style if you want to be safe.

## Config object is not a dictionary

Despite behaving like one, sometimes you need a "real" dict. The way to convert a
config node into one is to use the `to_dict` function.

```py
from gamma.config import get_config, to_dict

def do_something():
    config = get_config()
    val = config["foo"]
    val_dict = to_dict(val)
    assert type(val_dict) == dict
```


## Do not call get_config outside a wrapping function

It's a general good practice to avoid *side-effects* on `import`s. This is doubly true
when using `gamma-config`.

The first time you call `get_config`, the loading mechanism will load the config files
and cache the result. This may result in hard to debug behavior since you lose the
ability to extend `gamma-config`. For instance, reading custom tags before they're
loaded, not loading non-static config coming from a database, etc.

Example of bad behavior:

```py
from gamma.config import get_config

MY_CONSTANT = get_config()["my_value"]
```

Better:

```py
from gamma.config import get_config

def do_something():
    my_value = get_config()["my_value"]
```


## Config objects are immutable

Config objects (`RootConfig` and `ConfigNode` classes) are read-only and effectively
immutable. They're also fully pickable and you can pass them to child processes and
thread following the usual rules and they'll keep their dynamic behavior.

!>Note that in distributed processing, you're still required to be able to provide
`gamma-config` lib and dependencies as usual. In that case, rendering the (sub)config
to plain dict using `to_dict` is recommended.

The only way to mutate a config object is by using the `push_entry`. For the global
config returned from `get_config()`, you **must** modify it from the main thread;
`gamma-config` will complain if you try to modify it from another thread or
process.

```py
from gamma.config import get_config, push_entry

def do_something():
    config = get_config()
    patch = dict(foo=10)
    push_entry(config, "90-myentry", patch)
    assert config["foo"] == 10
```

The `push_entry(config, entry_key, entry)` function accept a `dict` or YAML string as
`entry` value. The `entry_key` is used to place the new entry in the correct order;
you most likely want to use a *high* number to ensure your config is inserted
with the highest priority.

## Applying validation and schemas

We don't force any specific validation method. But you're encouraged to validate and/or
enforce a schema in your configuration. And we try to play nice with most popular
validation libraries.

### Using Pydantic

One of the most convenient validation libraries is [Pydantic](https://pydantic-docs.helpmanual.io/).
While you can manually call `to_dict` or create [custom tags](/tags?id=writing-custom-tags),
a simple way is to use the [!obj](/tags?id=obj) tag pointing to `Pydantic` class.

Example:

```py
# in file myapp.config
from pydantic import BaseModel

class MySection(BaseModel):
    entry_a: int
    entry_b: str
    sub_obj: SubObj

class SubObj(BaseModel):
    foo: str
```

You can get a `MySection` instance directly:

```yaml
my_section: !obj:myapp.config:MySection
    entry_a: 1
    entry_b: "this is b"
    sub_obj:
        foo: bar
```

And in you application code:

```py
from gamma.config import get_config
from myapp.config import MySection

def do_something():
    config = get_config()

    val = config["my_section"]
    assert type(val) == MySection
    assert val.sub_obj.foo == "bar"
```
