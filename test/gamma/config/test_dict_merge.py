def test_merge():
    from gamma.config.dict_merge import merge

    # test simple
    target = {"foo": "bar"}
    patch = {"foo": "baz"}
    merge(target, patch)
    assert target["foo"] == "baz"

    # test dict merging
    target = {"foo": {"a": 1, "b": 2}}
    patch = {"foo": {"b": 20, "c": 30}}
    merge(target, patch)
    assert target == {"foo": {"a": 1, "b": 20, "c": 30}}

    # assert list merging
    target = {"foo": [1, 2]}
    patch = {"foo": [2, 3]}
    merge(target, patch)
    assert target == {"foo": [1, 2, 3]}

    # test type replacement (1)
    target = {"foo": [1, 2]}
    patch = {"foo": {"b": 20, "c": 30}}
    merge(target, patch)
    assert target == {"foo": {"b": 20, "c": 30}}

    # test type replacement (1)
    target = {"foo": {"a": 1, "b": 2}}
    patch = {"foo": [2, 3]}
    merge(target, patch)
    assert target == {"foo": [2, 3]}
