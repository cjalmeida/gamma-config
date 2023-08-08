from pydantic import BaseModel

from gamma.config import RootConfig, to_dict


class Dataset(BaseModel):
    path: str
    compression: str


def test_manual():
    src = """
datasets:
  foo:
    path: data/foo.csv.gz
    compression: gzip
  bar:
    path: data/bar.parquet
    compression: snappy
    """

    config = RootConfig("dummy", src)
    get_config = lambda: config  # noqa

    def get_dataset(name):
        entry = get_config()["datasets"][name]
        obj = Dataset(**to_dict(entry))
        return obj

    assert isinstance(get_dataset("foo"), Dataset)
    assert isinstance(get_dataset("bar"), Dataset)
