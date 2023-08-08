import time

import pytest

from gamma.config.confignode import (
    ConfigNode,
    RootConfig,
    config_context,
    push_entry,
    push_folder,
)
from gamma.config.globalconfig import get_config, set_config
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


def test_attribute_dot_access():
    META = SIMPLE + "\n__enable_dot_access__: True"
    cfg = RootConfig("00-meta.yaml", META)
    assert cfg.foo.bar == 1
    assert cfg.foo.zoo == [1, 2, 3]
    assert cfg.foo.sub.bar == 10

    with pytest.raises(AttributeError):
        assert bool(cfg.foo.notexist) == False  # noqa


def test_deprecated_dot_access():
    cfg = RootConfig(
        "dummy",
        """
        foo:
            bar: 1
        """,
    )

    assert cfg["foo"]["bar"] == 1

    with pytest.raises(ValueError, match="deprecated"):
        assert cfg.foo.bar == 1


def test_guards():
    with pytest.raises(Exception, match="entry"):
        RootConfig("foo: 1")

    cfg = RootConfig()
    push_entry(cfg, "abc", "foo: 1")

    assert cfg["foo"] == 1

    with pytest.raises(Exception, match="duplicated"):
        push_entry(cfg, "abc", "foo: 1")

    with pytest.raises(Exception, match="entry"):
        push_entry(cfg, "~abc", "foo: 1")


def test_config_context():
    cfg = RootConfig()
    push_entry(cfg, "abc", "foo: 1")

    assert cfg["foo"] == 1

    with config_context(cfg, "foo: 2"):
        assert cfg["foo"] == 2

    assert cfg["foo"] == 1

    set_config(cfg)
    with config_context("foo: 3"):
        get_config()["foo"] == 3

    assert cfg["foo"] == 1

    with pytest.raises(Exception):
        with config_context("foo: 3"):
            raise ValueError("Random exception")

    assert cfg["foo"] == 1

    # stress testing
    for _ in range(10):
        with pytest.raises(Exception):
            with config_context("foo: 3"):
                raise ValueError("Random exception")
        time.sleep(0.05)
        assert cfg["foo"] == 1


def test_push_folder():
    from pathlib import Path

    folder = Path(__file__).parent / "config_folder"

    cfg = RootConfig()
    push_entry(cfg, "10-base.yaml", SIMPLE)

    assert cfg["foo"]["bar"] != 1000
    assert cfg["foo"]["zit"] != 1000

    push_folder(cfg, folder)

    assert cfg["foo"]["bar"] == 1000
    assert cfg["foo"]["zit"] == 1000
