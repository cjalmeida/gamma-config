import os
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner


@pytest.fixture
def test_cwd():

    with tempfile.TemporaryDirectory() as td:
        cwd = os.getcwd()
        os.chdir(td)
        yield td
        os.chdir(cwd)


def test_scaffold(test_cwd):
    from gamma.config.cli_command import scaffold

    runner = CliRunner()

    # test cwd
    scaffold.callback(target=None, force=False)
    assert (Path(test_cwd) / "config/00-meta.yaml").exists()

    # test exists meta fail
    res = runner.invoke(scaffold)
    assert res.exit_code != 0

    # test target folder
    with tempfile.TemporaryDirectory() as td:
        res = scaffold.callback(target=td, force=False)
        assert (Path(td) / "config/00-meta.yaml").exists()
