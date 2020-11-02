import tempfile
from pathlib import Path
from gamma.config import get_config
import os
import sys
import pytest

META_STR = """
plugins:
    modules: ['foo.plugin']
"""

CONFIG_STR = """
test: !myenv USER
test2: !simple_env USER
"""


@pytest.fixture
def folder_fixture(monkeypatch):

    with tempfile.TemporaryDirectory() as td:
        base = Path(td)

        # create config/00-meta.yaml
        root = base / "config"
        root.mkdir()
        meta = root / "00-meta.yaml"
        meta.write_text(META_STR)

        # create config/10-test.yaml
        test_cfg = root / "10-test.yaml"
        test_cfg.write_text(CONFIG_STR)

        # create foo package
        foo = base / "foo"
        foo.mkdir()

        # copy plugin contents
        plugin = foo / "plugin.py"
        here = Path(__file__).parent
        src = here / "custom_plugin.py"
        plugin.write_text(src.read_text())

        # set config root
        monkeypatch.setenv("GAMMA_CONFIG_ROOT", str(root))

        # update sys.path
        sys.path.insert(0, str(td))

        yield

        # cleanup sys.path
        sys.path.pop(0)


def test_custom_plugins(folder_fixture):

    # load config
    config = get_config()

    assert config.test == os.getenv("USER")
    assert config.test2 == os.getenv("USER")
