import pytest
from gamma.config.load import load_node
from gamma.config.render import RenderDispatchError, render_node
from gamma.config.tags import Tag
from gamma.dispatch import dispatch
from ruamel.yaml.nodes import Node


def test_scalar_str():
    node_a = load_node("foo: bar")
    got = render_node(node_a)
    want = {"foo": "bar"}
    assert got == want


def test_scalar_seq():
    node_a = load_node("foo: [1, 2, 3]")
    got = render_node(node_a)
    want = {"foo": [1, 2, 3]}
    assert got == want


def test_scalar_int():
    assert render_node(load_node("foo: 99"))["foo"] == 99
    assert render_node(load_node("foo: 0o777"))["foo"] == 0o777
    assert render_node(load_node("foo: 0xBEEF"))["foo"] == 0xBEEF


def test_scalar_float():
    node_a = load_node("foo: 1.0")
    got = render_node(node_a)
    want = {"foo": 1.0}
    assert got == want


def test_scalar_null():
    assert render_node(load_node("foo: null"))["foo"] is None
    assert render_node(load_node("foo: Null"))["foo"] is None
    assert render_node(load_node("foo: NULL"))["foo"] is None
    assert render_node(load_node("foo: "))["foo"] is None
    assert render_node(load_node("foo: ~"))["foo"] is None


def test_scalar_bool():
    node_a = load_node("foo: True")
    node_b = load_node("foo: true")
    node_c = load_node("foo: TRUE")

    got_a = render_node(node_a)
    got_b = render_node(node_b)
    got_c = render_node(node_c)
    want = {"foo": True}
    assert got_a == want
    assert got_b == want
    assert got_c == want

    # YAML 1.2 requires only "true" and variants to autocast to bool
    assert render_node(load_node("foo: yes")) == {"foo": "yes"}
    assert render_node(load_node("foo: !!bool yes")) == {"foo": True}
    assert render_node(load_node("foo: !!bool no")) == {"foo": False}


def test_scalar_datetime():
    for v in ("2020-01-30", "2020-01-30T10:11:12", "2020-01-30T10:11:12Z"):
        node = load_node(f"foo: {v}")
        got = render_node(node)
        want = {"foo": v}  # should not render as date objects
        assert got == want


def test_scalar_nan():
    node = load_node("foo: .nan")
    got = render_node(node)["foo"]
    assert got != got  # NaN's are weird


def test_scalar_inf():
    node = load_node("foo: .inf")
    got = render_node(node)["foo"]
    assert got == float("inf")


def test_render_uri():
    from gamma.config import render_node

    src = """
    a: !foo     1
    b: !bar:b   2
    c: !bar:c   3
    """
    node = load_node(src)

    with pytest.raises(RenderDispatchError):
        render_node(node)

    Foo = Tag["!foo"]
    Bar = Tag["!bar"]
    BarC = Tag["!bar:c"]

    try:

        @dispatch
        def render_node(node: Node, tag: Foo, **ctx):
            return f"foo-{node.value}"

        @dispatch
        def render_node(node: Node, tag: Bar, **ctx):
            assert ctx["path"]
            return f"bar-{node.value}"

        @dispatch
        def render_node(node: Node, tag: BarC, **ctx):
            assert ctx.get("path") is None
            return f"bar-c-{node.value}"

        d = render_node(node)
        assert d["a"] == "foo-1"
        assert d["b"] == "bar-2"
        assert d["c"] == "bar-c-3"

    finally:
        del render_node[Node, Foo]
        del render_node[Node, Bar]
        del render_node[Node, BarC]
