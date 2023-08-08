import pytest


def test_default_ctx():
    from gamma.config import get_config
    from gamma.config.render_context import get_render_context

    get_config()  # requires initialization
    ctx = get_render_context()

    assert "include_folders" in ctx["c"]  # from 00-meta.yaml
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
