import multiprocessing as mp

def test_mock_subprocess(caplog, monkeypatch):

    from gamma.config import subprocess, get_config

    config = get_config()
    env = {}
    with subprocess.propagate_subprocess(env):
        new = subprocess.deserialize(env)
        assert not config._dump_mode
        assert not new._dump_mode
        assert new["sample_env"]["user"] == config["sample_env"]["user"]
        assert new["sample_env"]["secret_user"] == config["sample_env"]["secret_user"]


def _run_sub():
    from gamma.config import get_config
    new = get_config()
    assert not new._dump_mode
    assert new["environment"] == new.data["environment"] == "dev"


def test_actual_subprocess(caplog, monkeypatch):

    from gamma.config import subprocess

    env = {}
    with subprocess.propagate_subprocess(env) as (env_key, env_val):
        monkeypatch.setenv(env_key, env_val)
        proc = mp.Process(target=_run_sub)
        proc.start()
        proc.join()
    assert proc.exitcode == 0
