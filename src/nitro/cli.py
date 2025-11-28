"""Main CLI entry point for Nitro."""

import click
from rich.console import Console
from . import __version__
from .commands import scaffold, generate, serve, build, test, docs

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="nitro")
@click.pass_context
def main(ctx):
    """
    Nitro - A static website framework for the next generation.
    Build beautiful static websites using Python and YDNATL.
    """
    ctx.ensure_object(dict)


main.add_command(scaffold)
main.add_command(generate)
main.add_command(serve)
main.add_command(build)
main.add_command(test)
main.add_command(docs)


if __name__ == "__main__":
    main()
