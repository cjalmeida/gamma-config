# Structured configuration

!!! warning "`gamma.config.pydantic` deprecated"

    Prior to `v0.8` we had direct support for structured configuration. This was removed
    and replace with the recommended approach below.

For more complex applications, it's recommended to use an a approach called "Structured
Configuration" where you validate the provided configuration entries against a schema.
Python [provides _many_ ways](https://github.com/mahmoudimus/awesome-validation-python)
to validate a data structure against a schema. Here we'll [Pydantic][pydantic] as it's
very popular, easy to use and provide a number of useful features.

First let's start with an example where you declare "datasets" entries, and we have
different expected parameters for each format (eg. mandatory `separator` for CSV,
optional `columns` for Parquet).

```yaml
datasets:
  foo:
    format: csv
    path: data/foo.csv.gz
    compression: gzip
    separator: ";"

  bar:
    format: parquet
    path: data/bar.parquet
    compression: snappy
    columns: [col_x, col_y]
```

A first version of our code may create the following Pydantic model to handle this:

```python

from pydantic import BaseModel

class Dataset(BaseModel):                         # (1)
    format: str
    path: str
    compression: str
    separator: Optional[str]
    columns: Optional[List[str]]


def get_dataset(name: str) -> Dataset:            # (2)
    entry = get_config()["datasets"][name]        # (3)
    obj = Dataset(**to_dict(entry))               # (4)
    return obj
```

Here we create in `(1)` a Pydantic model, and an accessor function in `(2)`. In the
function implementation, we get the config entry `(3)`, convert to a plain dict using
`to_dict` to build the object from the dictionary.

The `to_dict` helper will recursively convert the nested config data structure to a
nested dictionary object, rendering dynamic values as needed. So, be aware of infinite
recursion for dynamic entries. Pydantic's `BaseModel(...)` knows how to handle
recursive dicts converting to the correct datatypes.

The fact we need to model mandatory format-specific attributes (eg. `separator` for CSV)
as `Optional` fields is not very clean though. Pydantic has [discriminated unions] that
allow us to split the specification into separate format-specific types.

```python
from typing import Literal

from beartype.typing import List, Optional, Union
from pydantic import BaseModel, Field, TypeAdapter
from typing_extensions import Annotated

from gamma.config import RootConfig, to_dict


class BaseDataset(BaseModel):
    format: str
    path: str


class ParquetDataset(BaseDataset):
    format: Literal["parquet"]
    compression: str
    columns: Optional[List[str]]


class CsvDataset(BaseDataset):
    format: Literal["csv"]
    compression: str
    separator: str


Dataset = TypeAdapter(
    Annotated[Union[ParquetDataset, CsvDataset], Field(discriminator="format")]
)


def get_dataset(name: str) -> Dataset:
    entry = get_config()["datasets"][name]
    obj = Dataset.validate_python(to_dict(entry))
    return obj

foo = get_dataset("foo")
bar = get_dataset("bar")

assert isinstance(foo, CsvDataset)
assert isinstance(bar, ParquetDataset)
```

In the modified full script example above:

- We import the types from stdlib `typing`, including `Literal`, and `Annotated` from
  `typing_extensions` or `typing` depending if you're on Python 3.9+. From pydantic,
  we import `Field` and `TypeAdapter` in addition to `BaseModel`.

- We create our Pydantic class structure mimicking our expected model. Note that while
  we use class inheritance here, this is not required.

- We declare our `Dataset` as being an "annotated" union of our target classes. We
  annotated it with a `Field` entry that provides the discriminator field. The
  `Annotated` type was specified PEP 593 and [here's the full documentation](https://docs.python.org/3/library/typing.html#typing.Annotated)
  Finally we wrap the annotated type in `TypeAdapter` to turn it into a full-fledged
  Pydantic model.

- In the `get_dataset` accessor, we modify it to use the `validate_python` method.

[pydantic]: https://docs.pydantic.dev/2.5/
[discriminated unions]: https://docs.pydantic.dev/2.5/concepts/unions/#discriminated-unions
