# flake8: noqa
# isort: skip_file

from gamma.config.__version__ import __version__

# register a scoped dispatcher
from plum import Dispatcher

dispatch = Dispatcher()


from ruamel.yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

from .builtin_tags import yaml
from .confignode import ConfigNode, RootConfig, config_context, push_entry, remove_entry
from .dump_dict import to_dict
from .dump_yaml import to_yaml
from .globalconfig import get_config, reset_config
from .render import render_node
from .render_context import ContextVar, context_providers
from .tags import Tag
from .findconfig import set_config_roots, is_config_roots_set, append_config_root
