"""Docs command for generating documentation."""

import click

from ..utils import info


@click.command()
@click.option(
    "--format",
    "-f",
    type=click.Choice(["html", "markdown"]),
    default="html",
    help="Output format for documentation",
)
@click.option("--output", "-o", default="docs", help="Output directory")
def docs(format, output):
    """
    Generate documentation for the site.

    Creates component docs and style guides.
    """
    info("Docs command - Coming soon!")
    info("This will generate documentation for your components.")
