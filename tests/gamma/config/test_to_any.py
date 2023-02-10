import io
from gamma.config import RootConfig, to_yaml, to_dict
from gamma.config.tags import Tag
from gamma.dispatch import dispatch
from ruamel.yaml.nodes import MappingNode
from ruamel.yaml import YAML


def test_to_dict_basic():
    # test simple case
    src = dict(a=1, b=2)
    cfg = RootConfig("dummy", src)
    d = to_dict(cfg)
    assert d == src
    assert type(d) == dict

    # test nested dicts
    src = dict(a=dict(b=1))
    cfg = RootConfig("dummy", src)
    d = to_dict(cfg)
    assert d == src
    assert type(d) == dict
    assert type(d["a"]) == dict

    # test nested dicts within lists
    src = dict(a=[dict(b=1), dict(c=2), dict(d=[dict(e=1)])])
    cfg = RootConfig("dummy", src)
    d = to_dict(cfg)
    assert d == src
    assert type(d) == dict
    assert type(d["a"]) == list
    assert type(d["a"][0]) == dict
    assert type(d["a"][1]) == dict
    assert type(d["a"][2]) == dict
    assert type(d["a"][2]["d"]) == list
    assert type(d["a"][2]["d"][0]) == dict
    assert type(d["a"][2]["d"][0]["e"]) == int


def test_custom_dict_tag():
    src = """
    foo: !customdict
        a: 1
    """

    from gamma.config.render import render_node

    CustomTag = Tag["!customdict"]
    try:

        @dispatch
        def render_node(node: MappingNode, tag: CustomTag, **ctx):
            # force render to dict even if tagged
            return to_dict(node)

        cfg = RootConfig("dummy", src)
        d = cfg["foo"]
        assert type(d) == dict
        assert d["a"] == 1
    finally:
        del render_node[MappingNode, CustomTag]


def test_to_yaml_basic():
    # test simple case
    src = dict(a=1, b=2)
    cfg = RootConfig("dummy", src)
    content = to_yaml(cfg)
    d = dict(YAML().load(io.StringIO(content)))
    assert d == src
