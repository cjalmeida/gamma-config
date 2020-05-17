import contextlib
import tempfile
import os
import pickle
from typing import Dict, Optional, Tuple

ENV_KEY = "GAMMA_CONFIG_SERIALIZED"


@contextlib.contextmanager
def propagate_subprocess(env: Optional[Dict[str, str]] = None) -> Tuple[str, str]:
    """Propagate the current config state to subprocesses.

    This is done by serialization, so any changes made in child processes are not
    propagated.

    Args:
        env: The env dict to update

    Returns:
        (env_key, env_value) of the environment updated
    """
    from gamma.config import get_config

    env = os.environ if env is None else env

    with tempfile.NamedTemporaryFile("wb") as tf:
        config = get_config()
        resolved = config.dump()
        pickle.dump(resolved, tf, pickle.HIGHEST_PROTOCOL)
        tf.flush()
        env[ENV_KEY] = tf.name
        yield ENV_KEY, tf.name
        del env[ENV_KEY]


def deserialize(env: Optional[Dict[str, str]] = None):
    env = os.environ if env is None else env
    _file = env[ENV_KEY]
    with open(_file, "rb") as ser:
        return pickle.load(ser)
