from gamma.config import RootConfig
from typing import List
from gamma.config import to_dict
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


def test_auto():
    src = """
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
    """

    config = RootConfig("dummy", src)
    get_config = lambda: config  # noqa

    def get_dataset(name):
        entry = get_config()["datasets"][name]
        obj = Dataset.parse_obj(to_dict(entry))
        return obj

    foo = get_dataset("foo")
    assert isinstance(foo, CsvDataset)
    assert foo.separator == ";"
    assert isinstance(get_dataset("bar"), ParquetDataset)
