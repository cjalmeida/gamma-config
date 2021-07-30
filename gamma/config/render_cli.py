import json
from argparse import ArgumentParser, RawTextHelpFormatter

from gamma.config import to_dict
from gamma.config.load import load_node


def render_cli(parser: ArgumentParser):
    descr = """Render VALUE on the stdout.

The VALUE may incorporate a custom tag (eg. `!j2 '{{ c.foo }}'`). If not provided,
we assume the value is a prefixed with `!ref`.

Examples:

    # render the value of "foo.bar", equivalent to "!ref foo.bar"
    python gamma.config render foo.bar

    # render a custom Jinja2 templated value
    python gamma.config render "!j2 /path/to/{{ c.foo.bar }}"

"""
    parser.description = descr
    parser.formatter_class = RawTextHelpFormatter

    parser.add_argument("value")
    parser.add_argument(
        "-o",
        "--output",
        choices=["raw", "json"],
        default="json",
        help="Output format, defaults to 'json'",
    )

    def _func(args):
        print(_do_render(args.value, args.output))

    parser.set_defaults(func=_func)
    return parser


def _do_render(value: str, output="json"):
    """Render a value and return as string.

    Args:
        output: either `raw` or `json`. Note `raw` only makes sense for scalars
    """

    if not value.startswith("!"):
        value = "!ref " + value.strip()

    node = load_node(value)
    data = to_dict(node)
    if output == "raw":
        return data
    elif output == "json":
        return json.dumps(data, indent=2)
    else:
        raise ValueError(f"Invalid output format: {output}")


if __name__ == "__main__":
    render_cli()
