"""Logging utilities for Nitro CLI."""

from enum import IntEnum
from typing import Optional
from rich.console import Console
from rich.panel import Panel
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
    """Display a formatted error panel."""
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


def step(current: int, total: int, message: str) -> None:
    """Log a step in a multi-step process."""
    if _level >= LogLevel.NORMAL:
        console.print(f"[dim][{current}/{total}][/dim] {message}")


def newline() -> None:
    """Print an empty line."""
    console.print()


def banner(subtitle: Optional[str] = None) -> None:
    """Display a branded banner."""
    text = Text()
    text.append("\n⚡ ", style="bold magenta")
    text.append("Nitro CLI", style="bold cyan")
    if subtitle:
        text.append(f" - {subtitle}", style="dim")
    text.append("\n")
    console.print(Panel(text, border_style="cyan", padding=(0, 2)))


def server_panel(host: str, port: int, live_reload: bool = True) -> None:
    """Display server info panel."""
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


def build_summary(stats: dict, elapsed: str) -> None:
    """Display build summary."""
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


def scaffold_complete(project_name: str) -> None:
    """Display scaffold completion message."""
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
    "server_panel",
    "build_summary",
    "scaffold_complete",
    "hmr_update",
]
