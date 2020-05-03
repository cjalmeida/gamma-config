from click.testing import CliRunner
import click


def test_cli_option():

    from gamma.config.cli import option, get_option
    from gamma.config.config import create_config_from_string

    @click.command()
    @option("-a", "--myarg")
    def foo(myarg):
        print(myarg)

    runner = CliRunner()

    res = runner.invoke(foo, ["-a", "hello-world"])
    assert res.exit_code == 0
    assert "hello-world" in res.output
    assert get_option("myarg") == "hello-world"

    content = """
        myarg: !cli myarg
        unset: !cli unset|mydefault
    """
    config = create_config_from_string(content)
    assert config["myarg"] == "hello-world"
    assert config["unset"] == "mydefault"
