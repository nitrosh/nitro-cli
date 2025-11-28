"""Enhanced logging utilities for Nitro CLI.

Provides production-quality logging with:
- Timestamps and contextual output
- Verbosity levels (quiet, normal, verbose, debug)
- Branded banners and panels
- Structured output for servers and builds
- Error formatting with context
- Log file support
"""

import sys
import socket
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import Optional, List, Dict, Any

from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.box import ROUNDED, HEAVY, SIMPLE
from rich.style import Style
from rich.traceback import Traceback


class LogLevel(IntEnum):
    """Log verbosity levels."""
    QUIET = 0    # Only errors and final summary
    NORMAL = 1   # Key milestones (default)
    VERBOSE = 2  # Detailed per-file output
    DEBUG = 3    # Full debug information


# Custom theme for Nitro CLI
NITRO_THEME = Theme({
    "info": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "bold red",
    "highlight": "magenta",
    "dim": "dim",
    "brand": "bold cyan",
    "brand.accent": "bold magenta",
    "path": "blue",
    "time": "dim cyan",
    "size": "green",
    "hmr": "yellow",
    "hmr.file": "bold yellow",
    "server.url": "bold green underline",
    "server.label": "dim",
})


class NitroLogger:
    """Enhanced logger for Nitro CLI with rich formatting."""

    VERSION = "0.1.0"

    def __init__(self):
        """Initialize the logger."""
        self.console = Console(theme=NITRO_THEME)
        self.level = LogLevel.NORMAL
        self.show_timestamps = False
        self.log_file: Optional[Path] = None
        self._file_console: Optional[Console] = None
        self._start_time: Optional[datetime] = None

    def configure(
        self,
        level: LogLevel = LogLevel.NORMAL,
        show_timestamps: bool = False,
        log_file: Optional[Path] = None,
    ) -> None:
        """Configure logger settings.

        Args:
            level: Verbosity level
            show_timestamps: Show timestamps in output
            log_file: Optional path to write logs
        """
        self.level = level
        self.show_timestamps = show_timestamps or level >= LogLevel.VERBOSE

        if log_file:
            self.log_file = Path(log_file)
            self._file_console = Console(
                file=open(self.log_file, "w"),
                theme=NITRO_THEME,
                force_terminal=False,
                no_color=True,
            )

    def set_level(self, level: LogLevel) -> None:
        """Set the verbosity level."""
        self.level = level
        if level >= LogLevel.VERBOSE:
            self.show_timestamps = True

    def start_timer(self) -> None:
        """Start the elapsed time timer."""
        self._start_time = datetime.now()

    def get_elapsed(self) -> str:
        """Get elapsed time since timer started."""
        if not self._start_time:
            return "0.00s"
        elapsed = (datetime.now() - self._start_time).total_seconds()
        if elapsed < 1:
            return f"{elapsed * 1000:.0f}ms"
        return f"{elapsed:.2f}s"

    def _timestamp(self) -> str:
        """Get formatted timestamp."""
        return datetime.now().strftime("%H:%M:%S")

    def _write(self, message: Any, style: Optional[str] = None) -> None:
        """Write to console and optionally to log file."""
        self.console.print(message, style=style)
        if self._file_console:
            self._file_console.print(message, style=style)

    def _format_message(self, prefix: str, message: str, style: str) -> Text:
        """Format a log message with optional timestamp."""
        text = Text()
        if self.show_timestamps:
            text.append(f"[{self._timestamp()}] ", style="time")
        text.append(prefix, style=style)
        text.append(f" {message}")
        return text

    # -------------------------------------------------------------------------
    # Basic logging methods
    # -------------------------------------------------------------------------

    def success(self, message: str) -> None:
        """Print a success message."""
        self._write(self._format_message("✓", message, "success"))

    def error(self, message: str) -> None:
        """Print an error message (always shown)."""
        self._write(self._format_message("✗", message, "error"))

    def warning(self, message: str) -> None:
        """Print a warning message."""
        if self.level >= LogLevel.QUIET:
            self._write(self._format_message("⚠", message, "warning"))

    def info(self, message: str) -> None:
        """Print an info message."""
        if self.level >= LogLevel.NORMAL:
            self._write(self._format_message("ℹ", message, "info"))

    def verbose(self, message: str) -> None:
        """Print a verbose message (only in verbose mode)."""
        if self.level >= LogLevel.VERBOSE:
            self._write(self._format_message("·", message, "dim"))

    def debug(self, message: str) -> None:
        """Print a debug message (only in debug mode)."""
        if self.level >= LogLevel.DEBUG:
            self._write(self._format_message("⋯", f"[DEBUG] {message}", "dim"))

    def print(self, *args, **kwargs) -> None:
        """Direct print to console (passthrough to Rich)."""
        self.console.print(*args, **kwargs)

    def newline(self) -> None:
        """Print an empty line."""
        self._write("")

    # -------------------------------------------------------------------------
    # Branded output
    # -------------------------------------------------------------------------

    def banner(self, subtitle: Optional[str] = None) -> None:
        """Display the Nitro CLI banner."""
        banner_text = Text()
        banner_text.append("⚡ ", style="brand.accent")
        banner_text.append("Nitro CLI", style="brand")
        banner_text.append(f" v{self.VERSION}", style="dim")

        content = Text()
        content.append("\n")
        content.append(banner_text)
        if subtitle:
            content.append(f"\n{subtitle}", style="dim")
        content.append("\n")

        panel = Panel(
            content,
            box=ROUNDED,
            border_style="cyan",
            padding=(0, 2),
        )
        self._write(panel)

    def section(self, title: str) -> None:
        """Print a section header."""
        if self.level >= LogLevel.NORMAL:
            self.newline()
            self._write(Text(f"─── {title} ", style="dim"))

    # -------------------------------------------------------------------------
    # Server output
    # -------------------------------------------------------------------------

    def server_panel(
        self,
        host: str,
        port: int,
        live_reload: bool = True,
        watching: Optional[str] = None,
    ) -> None:
        """Display the development server panel."""
        # Get local network IP
        network_ip = self._get_local_ip()

        content = Text()
        content.append("\n")

        # Local URL
        content.append("  Local:   ", style="server.label")
        content.append(f"http://{host}:{port}", style="server.url")
        content.append("\n")

        # Network URL (if available)
        if network_ip and host in ("0.0.0.0", "localhost", "127.0.0.1"):
            content.append("  Network: ", style="server.label")
            content.append(f"http://{network_ip}:{port}", style="server.url")
            content.append("\n")

        content.append("\n")

        # Status info
        content.append("  Live Reload: ")
        if live_reload:
            content.append("enabled", style="green")
        else:
            content.append("disabled", style="dim")
        content.append("\n")

        if watching:
            content.append("  Watching:    ")
            content.append(watching, style="path")
            content.append("\n")

        content.append("\n")

        panel = Panel(
            content,
            title="[bold]Development Server[/]",
            box=ROUNDED,
            border_style="green",
            padding=(0, 1),
        )
        self._write(panel)

    def _get_local_ip(self) -> Optional[str]:
        """Get the local network IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return None

    # -------------------------------------------------------------------------
    # HMR (Hot Module Reload) output
    # -------------------------------------------------------------------------

    def hmr_change(self, file_path: str) -> None:
        """Log a file change for HMR."""
        text = Text()
        if self.show_timestamps:
            text.append(f"[{self._timestamp()}] ", style="time")
        text.append("[HMR] ", style="hmr")
        text.append(file_path, style="hmr.file")
        text.append(" changed", style="hmr")
        self._write(text)

    def hmr_rebuilding(self, count: int = 1, target: str = "page") -> None:
        """Log that HMR is rebuilding."""
        plural = "s" if count > 1 else ""
        text = Text()
        if self.show_timestamps:
            text.append(f"[{self._timestamp()}] ", style="time")
        text.append("[HMR] ", style="hmr")
        text.append(f"Regenerating {count} {target}{plural}...", style="dim")
        self._write(text)

    def hmr_done(self, elapsed: Optional[str] = None) -> None:
        """Log that HMR rebuild is complete."""
        time_str = elapsed or self.get_elapsed()
        text = Text()
        if self.show_timestamps:
            text.append(f"[{self._timestamp()}] ", style="time")
        text.append("[HMR] ", style="hmr")
        text.append(f"Done in {time_str} ", style="dim")
        text.append("✓", style="success")
        self._write(text)

    # -------------------------------------------------------------------------
    # Build output
    # -------------------------------------------------------------------------

    def build_summary(
        self,
        stats: Dict[str, Any],
        build_dir: Path,
        elapsed: Optional[str] = None,
        optimizations: Optional[List[str]] = None,
    ) -> None:
        """Display a build summary table."""
        time_str = elapsed or self.get_elapsed()

        # Create the main stats table
        table = Table(
            box=ROUNDED,
            border_style="green",
            show_header=False,
            padding=(0, 2),
            expand=False,
        )
        table.add_column("Metric", style="dim")
        table.add_column("Value", style="green", justify="right")

        # Add type breakdown
        for file_type, size in stats.get("types", {}).items():
            if size > 0:
                count = stats.get("type_counts", {}).get(file_type, "")
                count_str = f" ({count} files)" if count else ""
                table.add_row(
                    f"{file_type.upper()} Files",
                    f"{self._format_size(size)}{count_str}"
                )

        # Add separator and totals
        table.add_row("", "")
        table.add_row("Total", f"{stats.get('count', 0)} files ({self._format_size(stats.get('total', 0))})")
        table.add_row("Time", time_str)

        # Create panel with table
        panel = Panel(
            table,
            title="[bold green]Build Complete[/]",
            border_style="green",
            padding=(1, 1),
        )
        self._write(panel)

        # Show optimizations if provided
        if optimizations:
            opt_content = Text()
            for i, opt in enumerate(optimizations):
                if i > 0:
                    opt_content.append("\n")
                opt_content.append("  ✓ ", style="success")
                opt_content.append(opt)
            opt_panel = Panel(
                opt_content,
                title="Optimizations Applied",
                border_style="dim",
                padding=(0, 1),
            )
            self._write(opt_panel)

    def file_generated(self, path: str, size: Optional[int] = None) -> None:
        """Log a generated file (verbose mode)."""
        if self.level >= LogLevel.VERBOSE:
            text = Text()
            if self.show_timestamps:
                text.append(f"[{self._timestamp()}] ", style="time")
            text.append("  → ", style="dim")
            text.append(path, style="path")
            if size is not None:
                text.append(f" ({self._format_size(size)})", style="size")
            self._write(text)

    def _format_size(self, size: int) -> str:
        """Format a file size in human-readable form."""
        if size < 1024:
            return f"{size}B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f}KB"
        else:
            return f"{size / (1024 * 1024):.1f}MB"

    # -------------------------------------------------------------------------
    # Error formatting
    # -------------------------------------------------------------------------

    def error_panel(
        self,
        title: str,
        message: str,
        file_path: Optional[str] = None,
        line: Optional[int] = None,
        column: Optional[int] = None,
        hint: Optional[str] = None,
    ) -> None:
        """Display a formatted error panel."""
        content = Text()
        content.append("\n")
        content.append(f"  {message}\n", style="error")

        if file_path:
            content.append("\n")
            location = f"  File: {file_path}"
            if line is not None:
                location += f", Line {line}"
            if column is not None:
                location += f", Column {column}"
            content.append(location + "\n", style="dim")

        if hint:
            content.append("\n")
            content.append(f"  Hint: {hint}\n", style="info")

        content.append("\n")

        panel = Panel(
            content,
            title=f"[bold red]{title}[/]",
            border_style="red",
            padding=(0, 1),
        )
        self._write(panel)

    def exception(self, exc: Exception, show_trace: bool = False) -> None:
        """Display an exception with optional traceback."""
        self.error(str(exc))

        if show_trace or self.level >= LogLevel.DEBUG:
            self._write(Traceback.from_exception(type(exc), exc, exc.__traceback__))

    # -------------------------------------------------------------------------
    # Progress helpers
    # -------------------------------------------------------------------------

    def step(self, current: int, total: int, message: str) -> None:
        """Log a step in a multi-step process."""
        if self.level >= LogLevel.NORMAL:
            text = Text()
            if self.show_timestamps:
                text.append(f"[{self._timestamp()}] ", style="time")
            text.append(f"[{current}/{total}] ", style="dim")
            text.append(message)
            self._write(text)

    # -------------------------------------------------------------------------
    # Scaffold output
    # -------------------------------------------------------------------------

    def scaffold_complete(self, project_name: str, template: str) -> None:
        """Display scaffold completion message."""
        content = Text()
        content.append("\n")
        content.append("  Project ")
        content.append(project_name, style="bold")
        content.append(" created successfully!\n")
        content.append(f"  Template: {template}\n")
        content.append("\n")
        content.append("  To get started:\n", style="dim")
        content.append(f"  cd {project_name}\n", style="cyan")
        content.append("  nitro serve\n", style="cyan")
        content.append("\n")

        panel = Panel(
            content,
            title="[bold green]Project Created[/]",
            border_style="green",
            padding=(0, 1),
        )
        self._write(panel)


# Global logger instance
_logger = NitroLogger()


# -------------------------------------------------------------------------
# Module-level convenience functions (backward compatible)
# -------------------------------------------------------------------------

def configure(
    level: LogLevel = LogLevel.NORMAL,
    show_timestamps: bool = False,
    log_file: Optional[Path] = None,
) -> None:
    """Configure the global logger."""
    _logger.configure(level, show_timestamps, log_file)


def set_level(level: LogLevel) -> None:
    """Set the verbosity level."""
    _logger.set_level(level)


def success(message: str) -> None:
    """Print a success message."""
    _logger.success(message)


def error(message: str) -> None:
    """Print an error message."""
    _logger.error(message)


def warning(message: str) -> None:
    """Print a warning message."""
    _logger.warning(message)


def info(message: str) -> None:
    """Print an info message."""
    _logger.info(message)


def verbose(message: str) -> None:
    """Print a verbose message."""
    _logger.verbose(message)


def debug(message: str) -> None:
    """Print a debug message."""
    _logger.debug(message)


# Export the logger instance and classes
logger = _logger
console = _logger.console

__all__ = [
    "NitroLogger",
    "LogLevel",
    "logger",
    "console",
    "configure",
    "set_level",
    "success",
    "error",
    "warning",
    "info",
    "verbose",
    "debug",
]