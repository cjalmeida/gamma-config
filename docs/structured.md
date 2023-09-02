# Structured configuration (Pydantic)

!!! warning "Deprecated"
    
    Structured configuration support is deprecated and scheduled for removal in `v1.0`.
    We recommend directly using [Pydantic's V2 discriminated unions](https://docs.pydantic.dev/latest/usage/types/unions/#discriminated-unions-aka-tagged-unions) 
    as an alternative.

While you can read configuration entries as dictionary entries, `gamma-config` has 
direct support for **structured configuration** using [Pydantic][pydantic]. Structured
configuration simply means using types to describe and validate your configuration
to catch potential issues ahead of time.


## Manually loading entries

```yaml
datasets:
  foo:
    path: data/foo.csv.gz
    compression: gzip
  bar:
    path: data/bar.parquet
    compression: snappy
```

You can use the following code to declare a structure that validate against our 
expected entries, and a helper function to read/validate this entry.

```python
from pydantic import BaseModel
from gamma.config import get_config, to_dict


class Dataset(BaseModel):
    path: str
    compression: str

def get_dataset(name):
    entry = get_config()["datasets"][name]
    obj = Dataset(**to_dict(entry))
    return obj

assert isinstance(get_dataset("foo"), Dataset)
assert isinstance(get_dataset("bar"), Dataset)
```

This approach is simple and flexible enough to work in most simple scenarios. 

## Using the `!obj` tag

A cleaner alternative that does not require a helper function is to use the [`!obj` tag](/tags/#obj)


```yaml
obj_default_module: mypackage.types

datasets:
  foo: !obj:Dataset
    path: data/foo.csv.gz
    compression: gzip
  bar: !obj:Dataset
    path: data/bar.parquet
    compression: snappy
```

And a similar code, but getting a `Dataset` instance directly

```python
from pydantic import BaseModel
from gamma.config import get_config, to_dict

class Dataset(BaseModel):
    path: str
    compression: str

foo = get_config()["datasets"]["foo"]
bar = get_config()["datasets"]["bar"]
assert isinstance(foo, Dataset)
assert isinstance(bar, Dataset)
```


## Automatically discriminating entries
Let's augment our example by having different expected parameters for each format 
(eg. `separator` for CSV, `columns` for Parquet).


```yaml
datasets:
  foo:
    kind: csv
    path: data/foo.csv.gz
    compression: gzip
    separator: ";"

  bar:
    kind: parquet
    path: data/bar.parquet
    compression: snappy
    columns: [col_x, col_y]
```

Here our simple approach might work, we just need to add code to `get_dataset` to
use the `kind` key to discriminate between the correct type. Because this is so 
common we provide the class `gamma.config.pydantic.ConfigStruct` to simplify the 
process.

```python
from typing import List
from pydantic import BaseModel
from gamma.config import get_config, to_dict
from gamma.config.pydantic import ConfigStruct

class Dataset(ConfigStruct):
    """Base class with common properties."""

    path: str
    compression: str

class CsvDataset(Dataset):
    kind = "csv"
    separator: str

class ParquetDataset(Dataset):
    kind = "parquet"
    columns: List[str]

def get_dataset(name):
    entry = get_config()["datasets"][name]
    obj = Dataset.parse_obj(to_dict(entry))
    return obj

foo = get_dataset("foo")
assert isinstance(foo, CsvDataset)
assert foo.separator == ";"
assert isinstance(get_dataset("bar"), ParquetDataset)
```

Note that we used `Dataset.parse_obj(<dict>)` function to instantiate and validate 
the correct Pydantic model. If we want to use the `!obj` tag in this situation, we can
create a `Datasets` wrapper function that will accept the value of the `datasets` key. 
Here's the modified YAML

```yaml
obj_default_module: mypackage.types

datasets: !obj:Datasets
  foo:
    kind: csv
    path: data/foo.csv.gz
    compression: gzip
    separator: ";"

  bar:
    kind: parquet
    path: data/bar.parquet
    compression: snappy
    columns: [col_x, col_y]
```

And the modified Python file:


```python
from typing import List
from pydantic import BaseModel
from gamma.config import get_config, to_dict
from gamma.config.pydantic import ConfigStruct

class Dataset(ConfigStruct):
    """Base class with common properties."""

    path: str
    compression: str

class CsvDataset(Dataset):
    kind = "csv"
    separator: str

class ParquetDataset(Dataset):
    kind = "parquet"
    columns: List[str]

# note we're using a function, not a class
def Datasets(**entries):
    return {key: Dataset.parse_obj(obj) for key, obj in entries.items() }
    
foo = get_config()["datasets"]["foo"]
bar = get_config()["datasets"]["bar"]
assert isinstance(foo, Dataset)
assert isinstance(bar, Dataset)
```


[pydantic]: https://pydantic-docs.helpmanual.io/
