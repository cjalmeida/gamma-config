# let's load the gamma-config plugins module
import os

from gamma.config import Node, Tag
from gamma.dispatch import dispatch

# create a tag handler for !myenv
MyEnvTag = Tag["!myenv"]


@dispatch
def render_node(node: Node, tag: MyEnvTag, **ctx) -> str:
    """Simplyfied !env tag without default handling"""
    env_val = os.getenv(node.value)
    return env_val
