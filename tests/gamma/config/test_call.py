import os

from gamma.config.confignode import RootConfig

SRC = """
t1: !call "os:getenv('FOO')"
t2: !call "os:getuid()"
t3: !call "os.path:join('foo','bar')"
t4: !call "os.path:join(os.path:join('a', 'b'), 'c')"
"""


def test_call(monkeypatch):
    cfg = RootConfig("dummy", SRC)
    monkeypatch.setenv("FOO", "foo")

    assert cfg["t1"] == "foo"
    assert cfg["t2"] == os.getuid()
    assert cfg["t3"] == os.path.join("foo", "bar")
    assert cfg["t4"] == os.path.join(os.path.join("a", "b"), "c")
