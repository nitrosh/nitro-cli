"""Logging utilities for Nitro CLI."""

from contextlib import contextmanager
from enum import IntEnum
from typing import Optional, Generator, Callable
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text


class LogLevel(IntEnum):
    QUIET = 0
    NORMAL = 1
    VERBOSE = 2
    DEBUG = 3


console = Console()
_level = LogLevel.NORMAL


def set_level(level: LogLevel) -> None:
    """Set the global log level."""
    global _level
    _level = level


def get_level() -> LogLevel:
    """Get the current log level."""
    return _level


def success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]✓[/green] {message}")


def error(message: str) -> None:
    """Print an error message."""
    console.print(f"[bold red]✗[/bold red] {message}")


def warning(message: str) -> None:
    """Print a warning message."""
    if _level >= LogLevel.QUIET:
        console.print(f"[yellow]⚠[/yellow] {message}")


def info(message: str) -> None:
    """Print an info message."""
    if _level >= LogLevel.NORMAL:
        console.print(f"[cyan]ℹ[/cyan] {message}")


def verbose(message: str) -> None:
    """Print a verbose message."""
    if _level >= LogLevel.VERBOSE:
        console.print(f"[dim]· {message}[/dim]")


def debug(message: str) -> None:
    """Print a debug message."""
    if _level >= LogLevel.DEBUG:
        console.print(f"[dim]⋯ [DEBUG] {message}[/dim]")


def panel(
    content: str,
    title: Optional[str] = None,
    style: str = "cyan",
) -> None:
    """Print content in a panel."""
    console.print(Panel(content, title=title, border_style=style))


def error_panel(
    title: str,
    message: str,
    file_path: Optional[str] = None,
    line: Optional[int] = None,
    hint: Optional[str] = None,
) -> None:
    """Display a formatted error panel.

    Falls back to simple text output if Rich rendering fails
    (e.g., when running in background threads without TTY).
    """
    try:
        content = Text()
        content.append(f"\n  {message}\n", style="red")

        if file_path:
            location = f"\n  File: {file_path}"
            if line:
                location += f", line {line}"
            content.append(location + "\n", style="dim")

        if hint:
            content.append(f"\n  Hint: {hint}\n", style="cyan")

        console.print(Panel(content, title=f"[bold red]{title}[/]", border_style="red"))
    except Exception:
        # Fallback for background threads or non-TTY environments
        print(f"\n✗ {title}: {message}")
        if file_path:
            location = f"  File: {file_path}"
            if line:
                location += f", line {line}"
            print(location)
        if hint:
            print(f"  Hint: {hint}")


def step(current: int, total: int, message: str) -> None:
    """Log a step in a multi-step process."""
    if _level >= LogLevel.NORMAL:
        console.print(f"[dim][{current}/{total}][/dim] {message}")


def newline() -> None:
    """Print an empty line."""
    console.print()


def banner(subtitle: Optional[str] = None) -> None:
    """Display a branded banner. (Deprecated: use header() instead)"""
    text = Text()
    text.append("\n⚡ ", style="bold magenta")
    text.append("Nitro CLI", style="bold cyan")

    if subtitle:
        text.append(f" - {subtitle}", style="dim")

    text.append("\n")
    console.print(Panel(text, border_style="cyan", padding=(0, 2)))


def header(action: str) -> None:
    """Display a simple action header."""
    console.print(f"\n[bold magenta]⚡[/] [bold]{action}[/]")


@contextmanager
def spinner(message: str) -> Generator[Callable[[str], None], None, None]:
    """Show a spinner during a long operation.

    Yields a function to update the spinner message.
    The spinner disappears when the context exits.

    Falls back to simple text output if Rich rendering fails
    (e.g., Rich 14.x Segment rendering issues).

    Usage:
        with spinner("Processing...") as update:
            update("Step 1...")
            do_step_1()
            update("Step 2...")
            do_step_2()
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(message, total=None)
            yield lambda msg: progress.update(task, description=msg)
    except Exception:
        # Fallback when Rich Progress cannot render (e.g., Rich 14.x compatibility)
        info(message)
        yield lambda msg: info(msg)


def server_ready(host: str, port: int, live_reload: bool = True) -> None:
    """Display server ready message."""
    reload_status = " [dim](live reload enabled)[/]" if live_reload else ""
    console.print(
        f"\n[green]✓[/] Ready at [bold green]http://{host}:{port}[/]{reload_status}\n"
    )


def server_panel(host: str, port: int, live_reload: bool = True) -> None:
    """Display server info panel. (Deprecated: use server_ready() instead)"""
    content = f"""
  Local:       [bold green]http://{host}:{port}[/]
  Live Reload: [green]{"enabled" if live_reload else "disabled"}[/]
"""
    console.print(
        Panel(content, title="[bold]Development Server[/]", border_style="green")
    )


def hmr_update(file_path: str, action: str = "changed") -> None:
    """Log HMR file change."""
    console.print(f"[yellow][HMR][/yellow] [bold yellow]{file_path}[/] {action}")


def build_complete(stats: dict, elapsed: str) -> None:
    """Display simple build complete message."""
    total = stats.get("total", 0)
    count = stats.get("count", 0)
    size = (
        f"{total / 1024:.1f}KB"
        if total < 1024 * 1024
        else f"{total / (1024 * 1024):.1f}MB"
    )
    console.print(f"\n[green]✓[/] Build complete: {count} files, {size} ({elapsed})")


def build_summary(stats: dict, elapsed: str) -> None:
    """Display build summary. (Deprecated: use build_complete() instead)"""
    total = stats.get("total", 0)
    count = stats.get("count", 0)
    size = (
        f"{total / 1024:.1f}KB"
        if total < 1024 * 1024
        else f"{total / (1024 * 1024):.1f}MB"
    )
    content = f"\n  Files: {count}\n  Size:  {size}\n  Time:  {elapsed}\n"
    console.print(
        Panel(content, title="[bold green]Build Complete[/]", border_style="green")
    )


def project_created(project_name: str) -> None:
    """Display simple project created message."""
    console.print(f"\n[green]✓[/] Created [bold]{project_name}[/]")
    console.print(f"\n  [dim]cd {project_name} && nitro dev[/]\n")


def scaffold_complete(project_name: str) -> None:
    """Display scaffold completion message. (Deprecated: use project_created() instead)"""
    content = f"""
  Project [bold]{project_name}[/] created!

  [dim]To get started:[/]
  [cyan]cd {project_name}[/]
  [cyan]nitro dev[/]
"""
    console.print(
        Panel(content, title="[bold green]Project Created[/]", border_style="green")
    )


__all__ = [
    "LogLevel",
    "console",
    "set_level",
    "get_level",
    "success",
    "error",
    "warning",
    "info",
    "verbose",
    "debug",
    "panel",
    "error_panel",
    "step",
    "newline",
    "banner",
    "header",
    "spinner",
    "server_panel",
    "server_ready",
    "build_summary",
    "build_complete",
    "scaffold_complete",
    "project_created",
    "hmr_update",
]
