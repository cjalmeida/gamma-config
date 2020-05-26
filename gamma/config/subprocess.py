import contextlib
import tempfile
import os
import pickle
import copy
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
        serialize(config, tf)
        tf.flush()
        env[ENV_KEY] = tf.name
        yield ENV_KEY, tf.name
        del env[ENV_KEY]


def serialize(config, stream):
    """Clone the config resolving the YAML tags.
    """

    original_dump_mode = config.dump_mode
    config.dump_mode = True
    new = copy.deepcopy(config)
    config.dump_mode = original_dump_mode

    # make sure the clone is a new root
    new._dump_mode = False
    new.parent = None
    assert new._root is new
    pickle.dump(new, stream, pickle.HIGHEST_PROTOCOL)


def deserialize(env: Optional[Dict[str, str]] = None):
    env = os.environ if env is None else env
    _file = env[ENV_KEY]
    with open(_file, "rb") as ser:
        return pickle.load(ser)
