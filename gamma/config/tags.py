import inspect
import itertools
import logging
from typing import Any, Callable, Dict, Optional

from .plugins import PROJECT_NAME, TagException, plugin_manager

_tags: Optional[Dict[str, Callable]] = None

logger = logging.getLogger(__name__)


def tag_handler_spec(tag: str, value: Any, root, dump: bool, node) -> Any:
    """Spec for tag handling functions.

    Functions may accept any argument (or none at all), as needed.

    Args:
        tag: The tag to be handled. Must match a declared TagSpec.
        value: The content of the tag. May be a scalar or a list, or a mapping type.
        root: The root Config object from which this tag was declared.
        dump: Flag indicating we're dumping the data to a potentially insecure
            destination, so sensitive data should not be returned.
        node: The raw YAML node. Can be returned during a dump to keep the field
            dynamic or hide sensitive values.

    Return:
        any value
    """


def get_tags(blacklist=True) -> Dict[str, Callable]:
    """Get tag and handlers"""
    from . import builtin_tags  # NOQA

    global _tags
    if _tags is None:
        blacklist_tags = set()
        if blacklist:
            from gamma.config import get_meta_config

            meta = get_meta_config()
            blacklist_tags = set(meta.get("blacklist_tags") or [])

        _tags = dict()
        plugin_manager.load_setuptools_entrypoints(PROJECT_NAME)
        plugins = plugin_manager.hook.add_tags()
        for tag_spec in itertools.chain(*plugins):
            tag = tag_spec.tag
            handler = tag_spec.handler

            if tag in blacklist_tags:
                logger.debug("Blacklisting tag: " + tag)
                continue

            if tag[0] != "!":
                msg = f"Invalid tag name '{tag}'. Missing '!'"
                raise TagException(msg)

            spec = inspect.getfullargspec(handler)
            handler_spec = inspect.getfullargspec(tag_handler_spec)
            valid_args = set(handler_spec.args) | set(handler_spec.kwonlyargs)
            args = set(spec.args) | set(spec.kwonlyargs)
            bogus = args - valid_args
            if bogus:
                raise TagException(f"Found unknown args in tag function '{bogus}'")

            _tags[tag] = handler
    return _tags
