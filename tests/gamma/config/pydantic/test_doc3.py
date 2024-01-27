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


TYPES = [ParquetDataset, CsvDataset]


def get_dataset_type():
    discr = Field(discriminator="format")
    field = Annotated[Union[tuple(TYPES)], discr]  # type: ignore
    return TypeAdapter(field)


def test_manual():
    src = """
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
    """

    config = RootConfig("dummy", src)
    get_config = lambda: config  # noqa

    def get_dataset(name):
        entry = get_config()["datasets"][name]
        Dataset = get_dataset_type()
        obj = Dataset.validate_python(to_dict(entry))
        return obj

    foo = get_dataset("foo")
    bar = get_dataset("bar")
    assert isinstance(foo, CsvDataset)
    assert not hasattr(foo, "columns")
    assert isinstance(bar, ParquetDataset)
    assert not hasattr(bar, "separator")
