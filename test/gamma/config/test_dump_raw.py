import os


def test_dump_raw():
    from gamma.config import config
    from ruamel.yaml import YAML

    yaml = YAML()

    src = """
    raw: !dump_raw
        bar: !j2 "{{ env.USER }}"

    normal:
        bar: !j2 "{{ env.USER }}"
    """

    config = config.create_config_from_string(src)
    assert config.normal.bar == os.getenv("USER")
    assert config.raw.bar == os.getenv("USER")

    dump = yaml.load(config.to_yaml())
    assert dump["normal"]["bar"] == os.getenv("USER")
    assert hasattr(dump["raw"]["bar"], "tag")
    assert dump["raw"]["bar"].tag.value == "!j2"
    assert dump["raw"]["bar"].value == "{{ env.USER }}"
