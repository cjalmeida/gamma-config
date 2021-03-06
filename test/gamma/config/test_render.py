from gamma.config.load import load_node
from gamma.config.render import render_node


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
    node_a = load_node("foo: 1")
    got = render_node(node_a)
    want = {"foo": 1}
    assert got == want


def test_scalar_float():
    node_a = load_node("foo: 1.0")
    got = render_node(node_a)
    want = {"foo": 1.0}
    assert got == want


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


def test_scalar_timestamp():
    from dateutil import parser

    for v in ("2020-01-30", "2020-01-30T10:11:12", "2020-01-30T10:11:12Z"):
        node = load_node(f"foo: {v}")
        got = render_node(node)
        want = {"foo": parser.parse(v)}
        assert got == want
