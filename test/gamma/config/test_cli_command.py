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
    runner.invoke(scaffold)
    assert (Path(test_cwd) / "config/00-meta.yaml").exists()

    # test exists meta fail
    res = runner.invoke(scaffold)
    assert res.exit_code != 0

    # test target folder
    with tempfile.TemporaryDirectory() as td:
        runner.invoke(scaffold, args=["-t", td])
        assert (Path(td) / "config/00-meta.yaml").exists()


def test_config_root_env(monkeypatch):
    from gamma.config.cli_command import scaffold

    with tempfile.TemporaryDirectory() as td:
        monkeypatch.setenv("GAMMA_CONFIG_ROOT", td + "/config")

        runner = CliRunner()

        # test scaffolding
        runner.invoke(scaffold, ["-t", td])
        assert (Path(td) / "config/00-meta.yaml").exists()

        # test loading
        from gamma.config import get_config

        config = get_config()
        assert config["sample_scalar_1"] == "hello world"
