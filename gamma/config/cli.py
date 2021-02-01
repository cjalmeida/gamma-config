from click import Option as ClickOption
from click import option as click_option

__all__ = ["option"]


class ConfigOption(ClickOption):

    processed_options = {}

    def full_process_value(self, ctx, value):
        _value = super().full_process_value(ctx, value)
        ConfigOption.processed_options[self.name] = _value
        return _value


def option(*args, **kwargs):
    kwargs.setdefault("cls", ConfigOption)
    return click_option(*args, **kwargs)


def get_option(key):
    return ConfigOption.processed_options[key]
