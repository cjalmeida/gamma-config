import os

import pytest


def test_load_sample(caplog, monkeypatch):
    import logging

    caplog.set_level(logging.DEBUG)

    from gamma.config import get_config
    from gamma.config.globalconfig import reset_config

    # load default config
    config = get_config()

    # assert meta was loaded
    config["include_folders"]  # should not fail

    # assert default was loaded
    assert config["sample_scalar_1"] == "hello world"
    assert config["sample_list_1"] == [1, 2, 3]

    # assert env was loaded and override default
    assert config["sample_scalar_2"] == "foobar_dev"
    assert config["deep"]["lvl1"]["lvl2"]["lvl3"] == "foobar_dev"

    # assert dot access
    config._dot_access = True
    assert config.sample_list_1 == [1, 2, 3]

    with pytest.raises(AttributeError):
        assert not config.missing

    with pytest.raises(AttributeError):
        assert not config._missing_underscore
    config._dot_access = False

    # reset config and test other env
    reset_config()
    monkeypatch.setenv("ENVIRONMENT", "prod")
    config = get_config()
    assert config["sample_scalar_2"] == "foobar_prod"
    assert config["deep"]["lvl1"]["lvl2"]["lvl3"] == "foobar_prod"
    assert config["deep"]["lvl1"]["lvl2"]["new"] == "new_prod"


def test_env_default(monkeypatch):
    from gamma.config import get_config

    config = get_config()

    # unset USER env to test default
    monkeypatch.delenv("USER", None)

    with pytest.raises(Exception):
        assert config["sample_env"]["user"]
    assert config["sample_env"]["default_1"] == "foo"
    assert config["sample_env"]["default_2"] is None


def test_sample_dump():
    from ruamel.yaml import YAML

    from gamma.config import get_config, to_dict, to_yaml

    # load default config
    config = get_config()
    assert config["sample_scalar_1"] == "hello world"

    # dump resolving tags
    dump = to_yaml(config, True)

    # load in a regular yaml loader
    yaml = YAML(typ="rt")
    loaded = yaml.load(dump)
    assert loaded["sample_scalar_1"] == "hello world"

    # test env
    assert loaded["sample_env"]["user"] == os.environ["USER"]

    # assert secret env was not dumped
    assert not isinstance(loaded["sample_env"]["secret_user"], str)
    assert isinstance(loaded["nested"]["composite"], str)
    assert not isinstance(loaded["nested"]["secret"], str)

    # dump again, with original tags
    dump = to_yaml(config, False)
    yaml = YAML(typ="rt")
    loaded = yaml.load(dump)
    assert not isinstance(loaded["sample_env"]["user"], str)
    assert hasattr(loaded["sample_env"]["user"], "tag")

    # dump partial config
    dump = to_yaml(config["sample_env"], True)
    yaml = YAML(typ="rt")
    loaded = yaml.load(dump)
    assert loaded["user"] == os.environ["USER"]

    # dump to dict
    new_dict = to_dict(config)
    assert type(new_dict) == dict
    assert type(new_dict["sample_env"]) == dict


def test_expression(monkeypatch):
    monkeypatch.setenv("USER", "dummy")
    import os

    from gamma.config import get_config

    config = get_config()

    assert config["sample_expr"]["expr_1"] == 2
    assert config["sample_expr"]["expr_2"] == "user=dummy"
    e3 = config["sample_expr"]["expr_3"]
    assert e3 == os.environ["USER"]
