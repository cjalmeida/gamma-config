import os
import tempfile
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
    assert (Path(test_cwd) / "config/00-meta.yaml").exists()

    # test exists meta fail
    with pytest.raises(SystemExit):
        scaffold(target=None, force=False)

    # test target folder
    with tempfile.TemporaryDirectory() as td:
        scaffold(target=td, force=False)
        assert (Path(td) / "config/00-meta.yaml").exists()
