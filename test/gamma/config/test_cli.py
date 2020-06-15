import click
from click.testing import CliRunner


def test_cli_option():

    from gamma.config.cli import option, get_option
    from gamma.config.config import create_config_from_string

    @click.command()
    @option("-a", "--arg-a")
    @option("-b", "--arg-b")
    @option("-c", "--arg-c", default="foo")
    def foo(arg_a, arg_b, arg_c):
        print(arg_a)

    runner = CliRunner()

    # declared option use value set, or config default, or explicit default
    res = runner.invoke(foo, ["-a", "hello-world"])
    assert res.exit_code == 0
    assert "hello-world" in res.output
    assert get_option("arg_a") == "hello-world"  # value set
    assert get_option("arg_c") == "foo"  # explicit default

    content = """
        myarg-a: !option arg_a|default-a
        myarg-b: !option arg_b|default-b
        myarg-c: !option arg_c|default-c
        unset: !option unset|mydefault
    """
    config = create_config_from_string(content)
    assert config["myarg-a"] == "hello-world"
    assert config["myarg-b"] == "default-b"
    assert config["myarg-c"] == "foo"

    # unset value
    assert config["unset"] == "mydefault"
