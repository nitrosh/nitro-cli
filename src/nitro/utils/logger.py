"""Logging utilities using rich for beautiful CLI output."""

from rich.console import Console
from rich.theme import Theme

custom_theme = Theme(
    {
        "info": "cyan",
        "success": "green",
        "warning": "yellow",
        "error": "bold red",
        "highlight": "magenta",
    }
)

console = Console(theme=custom_theme)
logger = console


def success(message: str) -> None:
    """Print a success message."""
    console.print(f"[success]✓[/success] {message}")


def error(message: str) -> None:
    """Print an error message."""
    console.print(f"[error]✗[/error] {message}")


def warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[warning]⚠[/warning] {message}")


def info(message: str) -> None:
    """Print an info message."""
    console.print(f"[info]ℹ[/info] {message}")
