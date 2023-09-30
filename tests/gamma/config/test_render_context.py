import pytest


def test_default_ctx():
    from gamma.config import get_config
    from gamma.config.render_context import get_render_context

    get_config()  # requires initialization
    ctx = get_render_context()

    assert ctx["env"]["USER"]


@pytest.fixture
def custom_ctx():
    import uuid

    from gamma.config import ContextVar, context_providers
    from gamma.config.cache import cache

    var_foo = ContextVar("foo", "bar")
    var_func = ContextVar("func", function=lambda: "zit")
    var_cache = ContextVar("cache", function=lambda: str(uuid.uuid4()), cacheable=True)
    var_rnd = ContextVar("rnd", function=lambda: str(uuid.uuid4()))
    prov = [var_foo, var_func, var_cache, var_rnd]

    var_foo2 = ContextVar("foo2", "bar")
    prov2 = lambda: [var_foo2]  # noqa

    context_providers.append(prov)
    context_providers.append(prov2)

    yield

    context_providers.pop()
    context_providers.pop()
    cache.clear()


def test_custom_ctx(custom_ctx):
    from gamma.config.render_context import get_render_context

    ctx = get_render_context()

    assert ctx["foo"] == "bar"
    assert ctx["func"] == "zit"
    old_cache = ctx["cache"]
    old_rnd = ctx["rnd"]

    ctx = get_render_context()
    new_cache = ctx["cache"]
    new_rnd = ctx["rnd"]

    assert new_cache == old_cache
    assert new_rnd != old_rnd

    assert ctx["foo2"] == "bar"


def test_underscore_context():
    from gamma.config import RootConfig

    src = """

_context:
  va: 1

na: !expr va

level0:
  _context:
    va: 10
    vb: 20

  na: !expr va
  nb: !expr vb

  level1:
    _context:
      va: 100
      vc: 300

    na: !expr va
    nb: !expr vb
    nc: !expr vc
    """

    cfg = RootConfig("dummy", src)

    assert cfg["na"] == 1
    assert cfg["level0"]["na"] == 10
    assert cfg["level0"]["level1"]["na"] == 100

    assert cfg["level0"]["nb"] == 20
    assert cfg["level0"]["level1"]["nb"] == 20

    assert cfg["level0"]["level1"]["nc"] == 300


def test_underscore_nested(monkeypatch):
    from gamma.config import RootConfig

    src = """

_context:
  foo: !call os:getenv("FOO")

sub:
  _context:
    bar: !call os:getenv("BAR")

  n1: !j2 "foo is {{ foo }}"
  n2: !j2 "bar is {{ bar }}"
"""

    monkeypatch.setenv("FOO", "foo")
    monkeypatch.setenv("BAR", "bar")

    cfg = RootConfig("dummy", src)
    assert cfg["sub"]["n1"] == "foo is foo"
    assert cfg["sub"]["n2"] == "bar is bar"
