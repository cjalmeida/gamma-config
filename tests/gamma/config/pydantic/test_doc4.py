from beartype.typing import List

from gamma.config import RootConfig
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
    return {key: Dataset.parse_obj(obj) for key, obj in entries.items()}


def test_auto2():
    from tests.gamma.config.pydantic.test_doc4 import CsvDataset, ParquetDataset

    src = """
obj_default_module: tests.gamma.config.pydantic.test_doc4

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
    """

    config = RootConfig("dummy", src)
    get_config = lambda: config  # noqa

    foo = get_config()["datasets"]["foo"]
    bar = get_config()["datasets"]["bar"]
    assert isinstance(foo, CsvDataset)
    assert isinstance(bar, ParquetDataset)
