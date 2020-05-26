def test_dict_sort():

    from gamma.config import config
    import json

    # Python 3.6+ guarantees dict keys ordering
    src = {"b": 1, "a": 2, "c": {"sub-b": 10, "sub-a": 20}}
    src_sorted = {"a": 2, "b": 1, "c": {"sub-a": 20, "sub-b": 10}}
    cfg = config.Config(src)

    d1 = cfg.to_dict()
    assert json.dumps(d1) == json.dumps(src)
    assert json.dumps(d1) != json.dumps(src_sorted)

    d2 = cfg.to_dict(sort=True)
    assert json.dumps(d2) != json.dumps(src)
    assert json.dumps(d2) == json.dumps(src_sorted)

    d3 = cfg.to_json()
    assert d3 == json.dumps(src)

    d4 = cfg.to_json(sort=True)
    assert d4 == json.dumps(src_sorted)


def test_to_dict_basic():

    from gamma.config import config

    # test simple case
    src = dict(a=1, b=2)
    cfg = config.Config(src)
    d = cfg.to_dict()
    assert d == src
    assert type(d) == dict

    # test nested dicts
    src = dict(a=dict(b=1))
    cfg = config.Config(src)
    d = cfg.to_dict()
    assert d == src
    assert type(d) == dict
    assert type(d["a"]) == dict

    # test nested dicts within lists
    src = dict(a=[dict(b=1), dict(c=2), dict(d=[dict(e=1)])])
    cfg = config.Config(src)
    d = cfg.to_dict()
    assert d == src
    assert type(d) == dict
    assert type(d["a"]) == list
    assert type(d["a"][0]) == dict
    assert type(d["a"][1]) == dict
    assert type(d["a"][2]) == dict
    assert type(d["a"][2]["d"]) == list
    assert type(d["a"][2]["d"][0]) == dict
    assert type(d["a"][2]["d"][0]["e"]) == int
