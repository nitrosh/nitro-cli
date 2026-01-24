"""Dev command - alias for serve with sensible defaults."""

import click
from .serve import serve


@click.command()
@click.option(
    "--port", "-p", default=3000, help="Port number for the development server"
)
@click.option(
    "--host", "-h", default="localhost", help="Host address for the development server"
)
@click.option("--no-reload", is_flag=True, help="Disable live reload")
@click.option(
    "--open", "-o", "open_browser", is_flag=True, help="Open browser automatically"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--debug", is_flag=True, help="Enable debug mode with full tracebacks")
@click.pass_context
def dev(ctx, port, host, no_reload, open_browser, verbose, debug):
    """
    Start a development server (alias for 'serve').

    This is the recommended command for local development.
    Watches for file changes and automatically reloads the browser.
    """
    # Invoke serve command with the same options
    ctx.invoke(
        serve,
        port=port,
        host=host,
        no_reload=no_reload,
        open_browser=open_browser,
        verbose=verbose,
        debug=debug,
    )
