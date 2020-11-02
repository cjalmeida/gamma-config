# let's load the gamma-config plugins module
import os
from gamma.config import plugins
import sys


# create a tag handler for !myenv

def myenv(value):
    """Simplyfied !env tag without default handling"""

    env_val = os.getenv(value)
    return env_val


# create a "hookimpl" to register the tag
# the hookimpl *must* be named "add_tags"

@plugins.hookimpl
def add_tags():
    """Add custom tags to gamma-config"""

    # you can have multiple "TagSpec" here.
    return [
        plugins.TagSpec("!myenv", myenv),
    ]


plugins.plugin_manager.register(sys.modules[__name__])


# use the simplified version
plugins.application_tags.append(plugins.TagSpec("!simple_env", myenv))
