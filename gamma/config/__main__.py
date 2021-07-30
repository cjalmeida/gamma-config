import argparse

# delegate to render_cli when called as a script
if __name__ == "__main__":
    from gamma.config.render_cli import render_cli

    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers()
    render_cli(subparsers.add_parser("render", help="Render config values"))

    args = parser.parse_args()
    func = getattr(args, "func", None)
    if func:
        func(args)
    else:
        parser.print_help()
