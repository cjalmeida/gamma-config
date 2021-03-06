from gamma.config.load import load_node
from gamma.config.rawnodes import get_item, get_values, is_equal, get_values, as_node


def test_get_item():
    # test simple
    left = load_node("foo: bar")
    right = load_node("foo: baz")

    assert is_equal(get_item(left, "foo"), "bar")
    assert is_equal(get_item(right, "foo"), "baz")


def test_get_values():
    # test simple
    node = load_node("[a, b, c]")

    items = get_values(node)
    expect = [as_node(x) for x in ["a", "b", "c"]]
    assert all([is_equal(a, b) for a, b in zip(items, expect)])
