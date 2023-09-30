# Writing configuration files

_Static_ configuration should be written as one or many YAML files. `gamma-config` by
will, by default, look for a `<current-working-dir>/config` folder, treating it as
_configuration root_. All YAML files in the base folder of this configuration root are
loaded and merged into a single data structure.

!!! note

    Sub-folders of the config roots **are not** loaded by default.

By convention, configurations are prefixed with two digits to ensure they're loaded
and merged in the correct order. Below is an example of a config folder structure:

```
<current-working-dir>/config
├── 10-sample.yaml
└── 11-sample-override.yaml
```

## Custom config root folder

If you need to set the config root folder to something else other than
`<current-working-dir>/config`, you can set the `GAMMA_CONFIG_ROOT` environment
variable to add one or more config folders. Folder paths must be separated by the system
path separator, (eg. `:` in Linux/MACOS, `;` in Windows).

You can also use the API functions `gamma.config.append_config_root` and
`gamma.config.set_config_roots` to add a folder or replace the set of root folders
respectively.

A common use-case is to place the configuration inside application package so it can be
included inside a `whl` as an alternative to Docker deployments. In this case, an
approach is to add the following snippet in your `<myapp>/__init__.py` file or your
preferred application entry-point, assuming you want to set `<myapp>/config` as your 
root folder:

```python
import os
from pathlib import Path
from gamma.config import set_config_roots
from . import config as config_root

# set correct configuration location, accepts either path strings or modules
set_config_roots([config_root])
```

## Merging behavior

The YAML files are sorted by file name, loaded and merged. The order of files matters
and to control the load order, by convention, we prefix the YAML files with a 2 digit
number. The merging then follows using a simple algorithm.

For example:

```yaml
# file: config/10-foo.yaml
sample_key:
  key_a: foo
  key_b: old
  key_c: [1, 2]
  key_d:
    foo: 10
    bar: 20
```

```yaml
# file: config/15-bar.yaml
sample_key:
  key_b: new
  key_c: [2, 3]
  key_d:
    foo: 15
  key_e: inserted
```

After loading the two files above, the resulting tree will look like:

```yaml
sample_key:
  key_a: foo
  key_b: new # updated
  key_c: [1, 2, 3] # ordered set union
  key_d:
    foo: 15 # updated
    bar: 20
  key_e: inserted # new key
```

If you want change the merge behavior for sequences (list) and mappings (dicts), you can
pass the special _hint_ comment `@hint: merge_replace` to fully replace the old value
with the new instead of trying to merge.

!!! note

    The `@hint` comment must be placed on the same line of the key you want to it to act on.

Example:

```yaml
# file: config/10-foo.yaml
sample_key:
  my_list: [1, 2]
  my_dict:
    foo: 10
    bar: 20
```

```yaml
# file: config/15-bar.yaml

sample_key:
  my_list: [2, 3] # @hint: merge_replace
  my_dict: # @hint: merge_replace
    foo: 15
```

And the output:

```yaml
sample_key:
  my_list: [2, 3]
  my_dict:
    foo: 15
```

## Dynamic values using tags

`gamma.config` allows you to add dynamic behavior to the configurations, while still
keeping them declarative, using YAML tags. This can be useful, for instance, for
providing parameters from environment variables, or avoiding repeating yourself using
references, or composing values using string interpolation.

YAML tags are annotations to entries using the `!` (exclamation mark) character that
changes the behavior of the entry. Below a simple example where we can get a value from
an environment variable:

```yaml
home: !env HOME
myvar: !env MYVAR
```

The values are fully dynamic and evaluated when you try to access them. For intance:

```python
import os
from gamma.config import get_config

config = get_config()

os.environ["MYVAR"] = "foo"
assert config["myvar"] == "foo"

os.environ["MYVAR"] = "bar"
# config will render the updated env variable
assert config["myvar"] == "bar"
```

There are many [built-in tags](../built-in-tags) that you can use, and
you can easily extend `gamma-config` to [support your own
tags](../custom-tags).
