"""Main CLI entry point for Nitro."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.box import ROUNDED
from . import __version__
from .commands import new, serve, dev, build, preview, clean, info, deploy, test, docs
from .core.project import get_project_root

console = Console()


def detect_project():
    """Detect if we're inside a Nitro project.

    Returns:
        tuple: (project_root, project_name) or (None, None)
    """
    project_root = get_project_root()
    if project_root:
        return project_root, project_root.name
    return None, None


def show_welcome():
    """Display the welcome banner with commands and project info."""
    project_root, project_name = detect_project()

    # Header with logo
    header = Text()
    header.append("\n")
    header.append("  ⚡ ", style="bold magenta")
    header.append("N I T R O", style="bold cyan")
    header.append("  ", style="bold magenta")
    header.append(f"v{__version__}", style="dim")
    header.append("\n")
    header.append("  Static websites for the next generation\n", style="dim")

    # Project info (if inside a project)
    if project_root:
        header.append("\n")
        header.append("  Project: ", style="dim")
        header.append(project_name, style="bold green")
        header.append("\n")
        header.append("  Path:    ", style="dim")
        header.append(str(project_root), style="blue")
        header.append("\n")

    # Commands section
    commands = Text()
    commands.append("\n")
    commands.append("  Commands:\n", style="bold")
    commands.append("    nitro new ", style="cyan")
    commands.append("<name>", style="dim cyan")
    commands.append("   Create a new project\n", style="dim")
    commands.append("    nitro dev         ", style="cyan")
    commands.append("   Start dev server with hot reload\n", style="dim")
    commands.append("    nitro build       ", style="cyan")
    commands.append("   Build for production\n", style="dim")
    commands.append("    nitro preview     ", style="cyan")
    commands.append("   Preview production build\n", style="dim")
    commands.append("    nitro clean       ", style="cyan")
    commands.append("   Clean build artifacts\n", style="dim")
    commands.append("    nitro info        ", style="cyan")
    commands.append("   Show project info\n", style="dim")
    commands.append("\n")
    commands.append("  Run ", style="dim")
    commands.append("nitro <command> --help", style="cyan")
    commands.append(" for more options\n", style="dim")

    content = Text()
    content.append_text(header)
    content.append_text(commands)

    panel = Panel(
        content,
        box=ROUNDED,
        border_style="cyan",
        padding=(0, 1),
    )
    console.print(panel)


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="nitro")
@click.pass_context
def main(ctx):
    """
    Nitro - A static website framework for the next generation.

    Build beautiful static websites using Python and nitro-ui.
    """
    ctx.ensure_object(dict)
    if ctx.invoked_subcommand is None:
        show_welcome()


main.add_command(new)
main.add_command(serve)
main.add_command(dev)
main.add_command(build)
main.add_command(preview)
main.add_command(clean)
main.add_command(info)
main.add_command(deploy)
main.add_command(test)
main.add_command(docs)


if __name__ == "__main__":
    main()
