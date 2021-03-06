import pytest
from gamma.config.confignode import ConfigNode, RootConfig, push_entry
from gamma.config.load import load_node

SIMPLE = """
foo:
    bar: 1
    zoo: [1, 2, 3]
    sub:
        bar: 10
    zit:
"""


def test_simple_config():

    node = load_node(SIMPLE)
    cfg = ConfigNode(node)
    assert isinstance(cfg["foo"], ConfigNode)
    assert cfg["foo"]["bar"] == 1
    assert cfg["foo"]["zoo"] == [1, 2, 3]
    assert cfg["foo"]["sub"]["bar"] == 10
    assert cfg["foo"]["zit"] is None


def test_attribute_access():
    node = load_node(SIMPLE)
    cfg = ConfigNode(node)
    assert cfg.foo.bar == 1
    assert cfg.foo.zoo == [1, 2, 3]
    assert cfg.foo.sub.bar == 10
    assert cfg.foo.zit is None
    assert isinstance(cfg.foo.notexist, ConfigNode)
    assert bool(cfg.foo.notexist) is False
    assert bool(cfg.foo) is True

    with pytest.raises(Exception):
        cfg.foo.notexist()


def test_guards():
    with pytest.raises(Exception, match="entry"):
        RootConfig("foo: 1")

    cfg = RootConfig()
    push_entry(cfg, "a", "foo: 1")

    assert cfg["foo"] == 1

    with pytest.raises(Exception, match="duplicated"):
        push_entry(cfg, "a", "foo: 1")
