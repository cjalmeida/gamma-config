import os

import pytest


def test_dump_raw():
    from gamma.config import config
    from ruamel.yaml import YAML

    yaml = YAML()

    src = """
    raw: !dump_raw
      bar: !j2 "{{ env.USER }}"
      nested:
        foo: !j2 "{{ env.USER }}"

    normal:
      bar: !j2 "{{ env.USER }}"

    myfunc: !func
      ref: os:getenv

    deep:
      nested:
        value: !ref normal.bar
    """

    cfg = config.create_config_from_string(src)
    assert cfg.normal.bar == os.getenv("USER")
    assert cfg.raw.bar == os.getenv("USER")

    # test to_dict
    dump = cfg.to_dict()
    assert not cfg._dump_mode
    assert dump["normal"]["bar"] == os.getenv("USER")
    assert hasattr(dump["raw"]["bar"], "tag")
    assert dump["raw"]["bar"].tag.value == "!j2"
    assert dump["raw"]["bar"].value == "{{ env.USER }}"

    # should affect nested when dumping parent or above
    assert dump["raw"]["nested"]["foo"].tag.value == "!j2"
    assert cfg.raw.to_dict()["nested"]["foo"].tag.value == "!j2"
    assert cfg.deep.nested.to_dict()["value"] == os.getenv("USER")
    assert not cfg._dump_mode

    # to_json should raise a type error because tags are not JSON serializable
    with pytest.raises(TypeError):
        dump = cfg.to_json()

    # parent !dump_raw should not affect children if called directly on the
    # nested mapping
    dump = cfg.raw.nested.to_dict()
    assert type(dump["foo"]) == str

    # test yaml
    dump = yaml.load(cfg.to_yaml())
    assert dump["normal"]["bar"] == os.getenv("USER")
    assert hasattr(dump["raw"]["bar"], "tag")
    assert dump["raw"]["bar"].tag.value == "!j2"
    assert dump["raw"]["bar"].value == "{{ env.USER }}"
