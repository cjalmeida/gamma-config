def test_ref():
    from gamma.config import builtin_tags

    # simple access
    config = {"foo": {"bar": 100}}
    val = builtin_tags.ref(value="foo.bar", root=config)
    assert val == 100

    # quoted access
    config = {"hello.world": {"bar": 100}}
    val = builtin_tags.ref(value="'hello.world'.bar", root=config)
    assert val == 100
