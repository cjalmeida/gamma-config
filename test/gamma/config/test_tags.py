def test_ref():
    from gamma.config import builtin_tags, Config

    # simple access
    config = Config({"foo": {"bar": 100}})
    val = builtin_tags.ref(value="foo.bar", root=config, dump=False)
    assert val == 100

    # quoted access
    config = Config({"hello.world": {"bar": 100}})
    val = builtin_tags.ref(value="'hello.world'.bar", root=config, dump=False)
    assert val == 100


def test_ref_sibling():
    from gamma.config import config
    from ruamel.yaml import YAML

    yaml = YAML()

    src = """
    a: foo
    b:
      ref_a: !ref a
      sib: !ref b.ref_a
    """

    cfg = config.create_config_from_string(src)
    assert cfg.a == "foo"
    assert cfg.b.ref_a == "foo"
    assert cfg.b.sib == "foo"

    dump = yaml.load(cfg.to_yaml())
    assert dump["b"]["ref_a"] == "foo"
