from gamma.config import render_node, RootConfig, ScalarNode
from gamma.config.builtin_tags import RefTag


def test_ref():

    # simple access
    root = RootConfig("dummy", {"foo": {"bar": 100}})
    node = ScalarNode("!ref", "foo.bar")
    val = render_node(node, RefTag(), root=root)
    assert val == 100

    # quoted access
    root = RootConfig("dummy", {"hello.world": {"bar": 100}})
    node = ScalarNode("!ref", "'hello.world'.bar")
    val = render_node(node, RefTag(), root=root)
    assert val == 100


def test_ref_sibling():
    src = """
    a: foo
    b:
      ref_a: !ref a
      sib: !ref b.ref_a
    """

    cfg = RootConfig("dummy", src)
    assert cfg.b.ref_a == "foo"
    assert cfg.a == "foo"
    assert cfg.b.sib == "foo"
