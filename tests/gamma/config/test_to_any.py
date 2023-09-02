import io

from ruamel.yaml import YAML
from ruamel.yaml.nodes import MappingNode

from gamma.config import RootConfig, dispatch, to_dict, to_yaml
from gamma.config.tags import Tag


def test_to_dict_basic():
    # test simple case
    src = dict(a=1, b=2)
    cfg = RootConfig("dummy", src)
    d = to_dict(cfg)
    assert d == src
    assert isinstance(d, dict)

    # test nested dicts
    src = dict(a=dict(b=1))
    cfg = RootConfig("dummy", src)
    d = to_dict(cfg)
    assert d == src
    assert isinstance(d, dict)
    assert isinstance(d["a"], dict)

    # test nested dicts within lists
    src = dict(a=[dict(b=1), dict(c=2), dict(d=[dict(e=1)])])
    cfg = RootConfig("dummy", src)
    d = to_dict(cfg)
    assert d == src
    assert isinstance(d, dict)
    assert isinstance(d["a"], list)
    assert isinstance(d["a"][0], dict)
    assert isinstance(d["a"][1], dict)
    assert isinstance(d["a"][2], dict)
    assert isinstance(d["a"][2]["d"], list)
    assert isinstance(d["a"][2]["d"][0], dict)
    assert isinstance(d["a"][2]["d"][0]["e"], int)


def test_custom_dict_tag():
    src = """
    foo: !test_any_customdict
        a: 1
    """

    from gamma.config.render import render_node

    CustomTag = Tag["!test_any_customdict"]

    @dispatch
    def render_node(node: MappingNode, tag: CustomTag, **ctx):
        # force render to dict even if tagged
        return to_dict(node)

    cfg = RootConfig("dummy", src)
    d = cfg["foo"]
    assert isinstance(d, dict)
    assert d["a"] == 1


def test_to_yaml_basic():
    # test simple case
    src = dict(a=1, b=2)
    cfg = RootConfig("dummy", src)
    content = to_yaml(cfg)
    d = dict(YAML().load(io.StringIO(content)))
    assert d == src


def test_secret_modifiers(monkeypatch):
    src = """
# test !env
foo: !env FOO
foo_show: !env:dump FOO

# test !expr
bar: !expr '"bar"'
bar_show: !expr:dump '"bar"'

# test !j2
zaz: !j2 "{{ 'zaz' }}"
zaz_secret: !j2:secret "{{ 'zaz' }}"

# test !call scalar
yyy: !call os:getenv("FOO")
yyy_show: !call:dump os:getenv("FOO")

# test !call mapping
owo: !call
    func: os:getenv
    key: FOO
owo_show: !call:dump
    func: os:getenv
    key: FOO
"""

    monkeypatch.setenv("FOO", "foo")

    cfg = RootConfig("dummy", src)
    content = to_yaml(cfg)
    d = dict(YAML().load(io.StringIO(content)))

    assert cfg["foo"] == "foo"
    assert d["foo"].tag.value == "!env"
    assert d["foo"].value == "FOO"
    assert d["foo_show"] == "foo"

    assert cfg["bar"] == "bar"
    assert d["bar"].tag.value == "!expr"
    assert d["bar"].value == '"bar"'
    assert d["bar_show"] == "bar"

    assert cfg["zaz"] == "zaz"
    assert d["zaz_secret"].tag.value == "!j2:secret"
    assert d["zaz_secret"].value == "{{ 'zaz' }}"
    assert d["zaz"] == "zaz"

    assert cfg["yyy"] == "foo"
    assert d["yyy"].tag.value == "!call"
    assert d["yyy"].value == 'os:getenv("FOO")'
    assert d["yyy_show"] == "foo"

    assert cfg["owo"] == "foo"
    assert d["owo"].tag.value == "!call"
    assert "func" in d["owo"]
    assert "key" in d["owo"]
    assert d["owo_show"] == "foo"
