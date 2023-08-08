import os


def test_pickle(monkeypatch):
    import pickle

    from gamma.config import get_config

    c1 = get_config()
    data = pickle.dumps(c1)
    assert data

    c2 = pickle.loads(data)

    assert c2 is not c1

    # check still dynamic
    assert c2["sample_env"]["user"] == os.getenv("USER")
    monkeypatch.setenv("USER", "foo")
    assert c2["sample_env"]["user"] == "foo"


def _sub(c, expected):
    assert c["sample_env"]["user"] == expected


def test_subprocess():
    import multiprocessing

    from gamma.config import get_config

    c = get_config()
    expected = c["sample_env"]["user"]
    p = multiprocessing.Process(target=_sub, args=(c, expected))
    p.start()
    p.join()
    assert p.exitcode == 0
