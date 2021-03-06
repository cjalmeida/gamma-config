from pathlib import Path
import os
import pytest
import subprocess
import shutil


@pytest.fixture
def prepare_fixture():
    here = Path(".").absolute()
    tmp = Path("./_tmp").absolute()
    tmp.mkdir(exist_ok=True)

    yield {"here": str(here), "_tmp": str(tmp)}

    os.chdir(here)
    # shutil.rmtree(tmp)


def test_find_jupyter(monkeypatch, prepare_fixture):
    from gamma.config.findconfig import get_config_root, FindJupyter
    from gamma.config import findconfig as mod

    expected_root = str(get_config_root())
    assert expected_root is not None

    # change to subfolder, can't find
    os.chdir("_tmp")
    with pytest.raises(Exception):
        get_config_root()

    # use findJupyter specialization
    monkeypatch.setattr(mod, "_isnotebook", lambda: True)
    jupyter_root = str(get_config_root(FindJupyter()))
    assert expected_root == jupyter_root

    os.chdir("..")

    # call using python in subfolder to assert we can't get a config root
    script = Path("_tmp") / "script.py"
    script.write_text(
        """
from gamma.config.findconfig import get_config_root
try:
    print(get_config_root())
except:
    print("None")
"""
    )
    env = {"PYTHONPATH": prepare_fixture["here"]}
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
    assert out == expected_root
