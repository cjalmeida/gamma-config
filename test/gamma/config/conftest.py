import pytest


@pytest.fixture(autouse=True)
def reset_config():
    """Reset config singletons on each test"""
    from gamma.config import config as config_mod

    config_mod.reset_config()


@pytest.fixture(autouse=True)
def autoset_user(monkeypatch):
    monkeypatch.setenv("USER", "dummy")
    yield
