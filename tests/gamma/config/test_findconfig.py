import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def prepare_fixture():
    here = Path(".").absolute()
    tmp = Path("./_tmp").absolute()
    tmp.mkdir(exist_ok=True)

    yield {"here": str(here), "_tmp": str(tmp)}

    os.chdir(here)
    # shutil.rmtree(tmp)


def test_find_jupyter(monkeypatch, prepare_fixture):
    from gamma.config import findconfig as mod
    from gamma.config.findconfig import get_config_roots

    expected_root = str(get_config_roots()[0])
    assert expected_root is not None

    # change to subfolder, can't find
    os.chdir("_tmp")
    with pytest.raises(Exception):
        get_config_roots()

    # use findJupyter specialization
    monkeypatch.setattr(mod, "_isnotebook", lambda: True)
    jupyter_root = str(get_config_roots("JUPYTER")[0])
    assert expected_root == jupyter_root

    os.chdir("..")

    # call using python in subfolder to assert we can't get a config root
    script = Path("_tmp") / "script.py"
    script.write_text(
        """
from gamma.config.findconfig import get_config_roots
try:
    print(get_config_roots()[0])
except:
    print("None")
"""
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = prepare_fixture["here"]
    cwd = "_tmp"
    python = shutil.which("python")
    cmd = [python, "script.py"]
    cp = subprocess.run(cmd, check=True, capture_output=True, env=env, cwd=cwd)
    out = cp.stdout.decode().strip()
    assert out == "None"

    # call using ipython in subfolder to check we CAN get a config root
    ipython = shutil.which("ipython")
    cmd = [ipython, "script.py"]
    cp = subprocess.run(cmd, check=True, capture_output=True, env=env, cwd=cwd)
    out = cp.stdout.decode().strip()
    assert out.endswith(expected_root)


@pytest.fixture
def multi_root():
    from gamma.config import set_config_roots

    META = """
include_folders: None
"""
    c1 = "{foo: 1, bar: 2}"
    t1 = tempfile.TemporaryDirectory()
    m1 = Path(t1.name) / "00-meta.yaml"
    m1.write_text(META)
    f1 = Path(t1.name) / "10-data.yaml"
    f1.write_text(c1)

    c2 = "{bar: 20, zzz: 30}"
    t2 = tempfile.TemporaryDirectory()
    m2 = Path(t2.name) / "01-meta.yaml"
    m2.write_text(META)
    f2 = Path(t2.name) / "20-data.yaml"
    f2.write_text(c2)

    yield t1.name, t2.name
    t1.cleanup()
    t2.cleanup()
    set_config_roots(None)


def test_multi_root(multi_root):
    from gamma.config import get_config, set_config_roots

    t1, t2 = multi_root

    set_config_roots([t1])
    cfg = get_config()
    assert cfg["foo"] == 1
    assert cfg["bar"] == 2

    set_config_roots([t2])
    cfg = get_config()
    assert cfg["bar"] == 20
    assert cfg["zzz"] == 30
    assert cfg.get("foo") is None

    set_config_roots([t1, t2])
    cfg = get_config()
    assert cfg["foo"] == 1
    assert cfg["bar"] == 20
    assert cfg["zzz"] == 30
