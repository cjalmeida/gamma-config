from gamma.config import RootConfig
from pydantic import BaseModel


class Dataset(BaseModel):
    path: str
    compression: str


def test_obj():
    from tests.gamma.config.pydantic.test_doc2 import Dataset

    src = """
obj_default_module: tests.gamma.config.pydantic.test_doc2

datasets:
  foo: !obj:Dataset
    path: data/foo.csv.gz
    compression: gzip
  bar: !obj:Dataset
    path: data/bar.parquet
    compression: snappy
    """

    config = RootConfig("dummy", src)
    get_config = lambda: config  # noqa

    foo = get_config()["datasets"]["foo"]
    bar = get_config()["datasets"]["bar"]
    assert isinstance(foo, Dataset)
    assert isinstance(bar, Dataset)
