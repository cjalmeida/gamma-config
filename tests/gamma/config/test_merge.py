from gamma.config.confignode import RootConfig, get_keys, push_entry
from gamma.config.load import load_node
from gamma.config.merge import merge_nodes
from gamma.config.render import render_node


def test_root_config_merge():
    root = RootConfig()

    a = "{foo: bar}"
    b = "{foo: baz, ping: pong}"
    push_entry(root, "a1", a)
    push_entry(root, "b1", b)
    assert root.foo == "baz"
    assert root.ping == "pong"

    keys = set([render_node(k) for k in get_keys(root)])
    assert keys == set(["foo", "ping"])


def test_merge():

    # test simple
    def _test(a, b, expect):
        left = "target", load_node(a)
        right = "patch", load_node(b)
        _, node = merge_nodes(*left, *right)
        got = render_node(node)
        assert got == expect

    a = "foo: bar"
    b = "foo: baz"
    expect = {"foo": "baz"}
    _test(a, b, expect)

    # test dict merging
    a = "foo: {a: 1, b: 2}"
    b = "foo: {b: 20, c: 30}"
    expect = {"foo": {"a": 1, "b": 20, "c": 30}}
    _test(a, b, expect)

    # test list merging
    a = "foo: [1, 2]"
    b = "foo: [2, 3]"
    expect = {"foo": [1, 2, 3]}
    _test(a, b, expect)

    # tes list of objects merging
    a = "foo: [{a: 1, b: 1}, {c: 1, d: 1}]"
    b = "foo: [{a: 2, b: 1}, {c: 1, d: 1}]"
    expect = {"foo": [{"a": 1, "b": 1}, {"c": 1, "d": 1}, {"a": 2, "b": 1}]}
    _test(a, b, expect)

    # test type replacement (1)
    a = "foo: [1, 2]"
    b = "foo: {b: 20, c: 30}"
    expect = {"foo": {"b": 20, "c": 30}}
    _test(a, b, expect)


def test_hints():

    # assert replace hint on inline lists
    target = load_node({"foo": [1, 2]})
    patch = load_node(
        """
        foo: [2, 3] # @hint: merge_replace
        """
    )
    _, node = merge_nodes(target, patch)
    assert render_node(node) == {"foo": [2, 3]}

    # assert replace hint on expanded lists
    target = load_node({"foo": [1, 2]})
    patch = load_node(
        """
        foo: # @hint: merge_replace
          # this comment should be ok
          - 2
          - 3
        """
    )
    _, node = merge_nodes(target, patch)
    assert render_node(node) == {"foo": [2, 3]}

    # test dict merging inline map
    target = load_node({"foo": {"a": 1, "b": 2}})
    patch = load_node(
        """
        foo: {"b": 20, "c": 30} # @hint: merge_replace
        """
    )
    _, node = merge_nodes(target, patch)
    assert render_node(node) == {"foo": {"b": 20, "c": 30}}

    # test dict merging expanded map
    target = load_node({"foo": {"a": 1, "b": 2}})
    patch = load_node(
        """
        foo:  # @hint: merge_replace
          b: 20
          c: 30
        """
    )
    _, node = merge_nodes(target, patch)
    assert render_node(node) == {"foo": {"b": 20, "c": 30}}

    # test some hint syntax variants - 1
    target = load_node({"foo": {"a": 1, "b": 2}})
    patch = load_node(
        """
        foo: {"b": 20, "c": 30} #@hint: merge_replace
        """
    )
    _, node = merge_nodes(target, patch)
    assert render_node(node) == {"foo": {"b": 20, "c": 30}}

    # test some hint syntax variants - 2
    target = load_node({"foo": {"a": 1, "b": 2}})
    patch = load_node(
        """
        foo: {"b": 20, "c": 30} #@hint:   merge_replace
        """
    )
    _, node = merge_nodes(target, patch)
    assert render_node(node) == {"foo": {"b": 20, "c": 30}}
