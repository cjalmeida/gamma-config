import multiprocessing as mp
import threading
import pytest


def test_mock_subprocess(caplog):

    from gamma.config import subprocess, get_config

    config = get_config()
    env = {}
    with subprocess.propagate_subprocess(env):
        new = subprocess.deserialize(env)
        assert not config.dump_mode
        assert not new.dump_mode
        assert new["sample_env"]["user"] == config["sample_env"]["user"]
        assert new["sample_env"]["secret_user"] == config["sample_env"]["secret_user"]


def _run_sub():
    from gamma.config import get_config, config as config_mod

    print("sub", config_mod._config_store)
    new = get_config()
    assert not new._dump_mode
    assert new["environment"] == new.data["environment"] == "dev"


def test_actual_subprocess(monkeypatch, caplog):

    from gamma.config import subprocess, config as config_mod

    print("local", config_mod._config_store)

    env = {}
    with subprocess.propagate_subprocess(env) as (env_key, env_val):
        monkeypatch.setenv(env_key, env_val)
        proc = mp.Process(target=_run_sub)
        # proc = threading.Thread(target=_run_sub)
        proc.start()
        proc.join()
    assert proc.exitcode == 0


def test_local_store_thread():
    from gamma.config.config import LocalStore

    _local_store = LocalStore()
    # _local_store = threading.local()
    _local_store.foo = 100

    def _sub():
        assert not hasattr(_local_store, "foo")
        _local_store.foo = 200
        assert _local_store.foo == 200

    # expected single thread behavior
    assert _local_store.foo == 100
    with pytest.raises(AssertionError):
        _sub()  # same thread

    assert _local_store.foo == 100

    # expect behavior similar to threading.local for another thread
    t = threading.Thread(target=_sub)
    t.start()
    t.join()

    assert _local_store.foo == 100

    # expect thread-local behavior but with forked process
    p = mp.Process(target=_sub)
    p.start()
    p.join()
    assert p.exitcode == 0  # this fails if you use threading.local as store

    del _local_store.foo

    with pytest.raises(AttributeError):
        assert _local_store.foo == 100
    assert not hasattr(_local_store, "foo")
