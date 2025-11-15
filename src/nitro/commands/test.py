"""Test command for site quality checks."""

import click
from ..utils import info


@click.command()
@click.option("--coverage", "-c", is_flag=True, help="Generate coverage report")
@click.option("--watch", "-w", is_flag=True, help="Watch mode for continuous testing")
@click.option(
    "--type",
    "-t",
    type=click.Choice(["all", "validation", "accessibility", "links", "performance"]),
    default="all",
    help="Type of tests to run",
)
def test(coverage, watch, type):
    """Run tests on the static site.

    Validates HTML, checks accessibility, and more.
    """
    info("Test command - Coming soon!")
    info("This will run quality checks on your site.")
