from beartype.typing import List, Optional
from pydantic import BaseModel

from gamma.config import RootConfig, to_dict


class Dataset(BaseModel):
    format: str
    path: str
    compression: str
    separator: Optional[str]
    columns: Optional[List[str]]


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
        obj = Dataset(**to_dict(entry))
        return obj

    foo = get_dataset("foo")
    bar = get_dataset("bar")
    assert isinstance(foo, Dataset)
    assert foo.columns is None
    assert isinstance(bar, Dataset)
    assert bar.separator is None
