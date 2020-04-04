import os


def test_load_sample(caplog, monkeypatch):
    import logging

    caplog.set_level(logging.DEBUG)

    from gamma.config import get_config, config as config_mod

    # load default config
    config = get_config()

    # assert meta was loaded
    assert config["environment"] == "dev"

    # assert default was loaded
    assert config["sample_scalar_1"] == "hello world"
    assert config["sample_list_1"] == [1, 2, 3]

    # assert env was loaded and override default
    assert config["sample_scalar_2"] == "foobar_dev"

    # reset config and test other env
    config_mod._config = None
    config_mod._meta_config = None
    monkeypatch.setenv("ENVIRONMENT", "prod")
    config = get_config()
    assert config["environment"] == "prod"
    assert config["sample_scalar_2"] == "foobar_prod"


def test_sample_dump():
    from gamma.config import get_config
    from ruamel.yaml import YAML

    # load default config
    config = get_config()
    assert config["environment"] == "dev"

    # dump resolving tags
    dump = config.to_yaml(resolve_tags=True)

    # load in a regular yaml loader
    yaml = YAML(typ="rt")
    loaded = yaml.load(dump)
    assert loaded["environment"] == "dev"

    # assert secret env was not dumped
    assert loaded["sample_env"]["user"] == os.environ["USER"]
    assert not isinstance(loaded["sample_env"]["secret_user"], str)

    # dump again, with original tags
    dump = config.to_yaml(resolve_tags=False)
    yaml = YAML(typ="rt")
    loaded = yaml.load(dump)
    assert not isinstance(loaded["environment"], str)
    assert hasattr(loaded["environment"], "tag")


def test_expression():
    from gamma.config import get_config
    import os

    config = get_config()

    assert config["sample_expr"]["expr_1"] == 2

    e3 = config["sample_expr"]["expr_3"]
    assert e3 == os.environ["USER"]