from typing import List

from gamma.config.pydantic import DictConfigType
from pydantic import BaseModel
from ruamel.yaml import YAML

CONFIG = """
objects:
    foo:
        kind: foo
        value: 100
    bar:
        kind: bar
        custom: 200
    foo_str: 300

lists:
    - kind: foo
      value: 100
    - kind: bar
      custom: 200
"""

yaml = YAML()


class CustomType(DictConfigType):
    @classmethod
    def parse_scalar(cls, value):
        return Foo(value=value)


class Foo(CustomType):
    kind = "foo"
    value: int


class Bar(CustomType):
    kind = "bar"
    custom: int


class Objects(BaseModel):
    foo: CustomType
    bar: CustomType
    foo_str: CustomType


class _TestConfig(BaseModel):
    objects: Objects
    lists: List[CustomType]


def test_load_pydantic():
    config = _TestConfig(**yaml.load(CONFIG))
    objs = config.objects
    assert objs
    assert objs.foo.value == 100
    assert objs.bar.custom == 200
    assert objs.foo_str.value == 300

    lists = config.lists
    lists[0].kind == "foo"
    lists[1].kind == "bar"
