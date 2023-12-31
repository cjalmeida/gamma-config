import pytest


def test_as_node():
    from gamma.config import render_node
    from gamma.config.rawnodes import as_node

    # just check reflexivity
    assert render_node(as_node(1)) == 1
    assert render_node(as_node("a")) == "a"
    assert render_node(as_node(1.0)) == 1.0
    assert render_node(as_node(None)) is None
    assert render_node(as_node(False)) is False
    assert render_node(as_node(True)) is True

    a = as_node(as_node(1))
    b = as_node(1)
    assert a.tag == b.tag and a.value == b.value

    class Custom:
        pass

    with pytest.raises(Exception):
        as_node(Custom())


def test_equals():
    from gamma.config.rawnodes import as_node, is_equal

    # fallback equality
    assert is_equal("foo", "foo")

    a = as_node([1, 2, 3])
    b = as_node([1, 2, 3])
    assert is_equal(a, b)
