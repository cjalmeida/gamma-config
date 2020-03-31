import pytest


@pytest.fixture(autouse=True)
def reset_config():
    from gamma.config import config as config_mod

    config_mod._config = None
    config_mod._meta_config = None
