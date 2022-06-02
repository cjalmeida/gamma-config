import os
import tempfile
import time
from pathlib import Path

import pytest


@pytest.fixture
def test_cwd():

    with tempfile.TemporaryDirectory() as td:
        cwd = os.getcwd()
        os.chdir(td)
        yield td
        os.chdir(cwd)


def test_scaffold(test_cwd):
    from gamma.config.scaffold import scaffold

    # test cwd
    scaffold(target=None, force=False)
    meta = Path(test_cwd) / "config/00-meta.yaml"
    assert meta.exists()
    expect = meta.stat().st_ctime_ns

    # assert no overwrite
    time.sleep(0.1)
    scaffold(target=None, force=False)
    got = meta.stat().st_ctime_ns
    assert expect == got

    # test target folder
    with tempfile.TemporaryDirectory() as td:
        scaffold(target=td, force=False)
        assert (Path(td) / "config/00-meta.yaml").exists()
