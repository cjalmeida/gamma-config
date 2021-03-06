def test_to_dict_basic():

    from gamma.config import render_node, RootConfig

    # test simple case
    src = dict(a=1, b=2)
    cfg = RootConfig("dummy", src)
    d = render_node(cfg)
    assert d == src
    assert type(d) == dict

    # test nested dicts
    src = dict(a=dict(b=1))
    cfg = RootConfig("dummy", src)
    d = render_node(cfg)
    assert d == src
    assert type(d) == dict
    assert type(d["a"]) == dict

    # test nested dicts within lists
    src = dict(a=[dict(b=1), dict(c=2), dict(d=[dict(e=1)])])
    cfg = RootConfig("dummy", src)
    d = render_node(cfg)
    assert d == src
    assert type(d) == dict
    assert type(d["a"]) == list
    assert type(d["a"][0]) == dict
    assert type(d["a"][1]) == dict
    assert type(d["a"][2]) == dict
    assert type(d["a"][2]["d"]) == list
    assert type(d["a"][2]["d"][0]) == dict
    assert type(d["a"][2]["d"][0]["e"]) == int
