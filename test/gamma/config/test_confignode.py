from gamma.config.load import load_node
from gamma.config.confignode import ConfigNode


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

