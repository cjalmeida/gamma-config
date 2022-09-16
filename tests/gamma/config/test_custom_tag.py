import os
import sys
import tempfile
from pathlib import Path

import pytest
from gamma.config import get_config

CONFIG_STR = """
test: !myenv USER
test2: !env USER
"""


@pytest.fixture
def folder_fixture(monkeypatch):

    with tempfile.TemporaryDirectory() as td:
        base = Path(td)

        # create config/00-meta.yaml
        root = base / "config"
        root.mkdir()
        meta = root / "00-meta.yaml"
        meta.write_text("include_folders: []")

        # create config/10-test.yaml
        test_cfg = root / "10-test.yaml"
        test_cfg.write_text(CONFIG_STR)

        # create foo package
        foo = base / "foo"
        foo.mkdir()

        # copy plugin contents
        plugin = foo / "custom_tag.py"
        here = Path(__file__).parent
        src = here / "custom_tag.py"
        plugin.write_text(src.read_text())

        # copy config envs
        for src in (here / ".env", here / ".env"):
            dst = base / src.name
            dst.write_text(src.read_text())

        # set config root
        monkeypatch.setenv("GAMMA_CONFIG_ROOT", str(root))

        # update sys.path
        sys.path.insert(0, str(td))

        yield

        # cleanup sys.path
        sys.path.pop(0)

        # cleanup os.environ
        del os.environ["DUMMY_ENV"]


def test_custom_plugins(folder_fixture):
    import foo.custom_tag  # noqa
    from gamma.config import render_node, ScalarNode, Tag

    # check dispatch correctly added the custom renderer
    assert render_node[ScalarNode, Tag["!myenv"]] is not None

    # load config
    config = get_config()

    assert config["test"] == os.getenv("USER")
    assert config["test2"] == os.getenv("USER")
    assert os.getenv("DUMMY_ENV")
