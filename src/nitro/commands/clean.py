"""Clean command - remove build artifacts and cache."""

import shutil
from pathlib import Path

import click

from ..core.config import load_config
from ..core.page import get_project_root
from ..utils import info, success, warning, error, header, spinner, newline


@click.command()
@click.option("--build", "clean_build", is_flag=True, help="Clean only build directory")
@click.option("--cache", "clean_cache", is_flag=True, help="Clean only cache directory")
@click.option(
    "--all", "clean_all", is_flag=True, help="Clean everything (build + cache)"
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would be deleted without deleting"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def clean(clean_build, clean_cache, clean_all, dry_run, verbose):
    """Clean build artifacts and cache."""
    project_root = get_project_root()
    if not project_root:
        project_root = Path.cwd()

    config_path = project_root / "nitro.config.py"
    if config_path.exists():
        config = load_config(config_path)
        build_dir = project_root / config.build_dir
    else:
        build_dir = project_root / "build"

    cache_dir = project_root / ".nitro"

    if not clean_build and not clean_cache and not clean_all:
        clean_all = True

    directories_to_clean = []

    if clean_all or clean_build:
        directories_to_clean.append(("build", build_dir))
    if clean_all or clean_cache:
        directories_to_clean.append(("cache", cache_dir))

    if dry_run:
        header("Clean (dry run)")
        info("The following would be deleted:")
        newline()

        total_size = 0
        for name, dir_path in directories_to_clean:
            if dir_path.exists():
                size = _get_dir_size(dir_path)
                total_size += size
                info(f"  {name}: {dir_path} ({_format_size(size)})")
            elif verbose:
                warning(f"{name.capitalize()} directory not found: {dir_path}")

        newline()
        info(f"Total: {_format_size(total_size)} would be freed")
        return

    header("Cleaning build artifacts...")

    total_size = 0
    cleaned_count = 0

    with spinner("Cleaning...") as update:
        for name, dir_path in directories_to_clean:
            if dir_path.exists():
                update(f"Removing {name}...")
                size = _get_dir_size(dir_path)
                total_size += size

                try:
                    shutil.rmtree(dir_path)
                    cleaned_count += 1
                except Exception as e:
                    error(f"Failed to remove {name}: {e}")
            elif verbose:
                warning(f"{name.capitalize()} directory not found: {dir_path}")

    if cleaned_count > 0:
        success(
            f"Cleaned {cleaned_count} director{'ies' if cleaned_count > 1 else 'y'}, freed {_format_size(total_size)}"
        )
    else:
        info("Nothing to clean")


def _get_dir_size(path: Path) -> int:
    """Calculate total size of directory in bytes."""
    total = 0
    try:
        for entry in path.rglob("*"):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                except (OSError, PermissionError):
                    # Skip files we can't stat
                    pass
    except (OSError, PermissionError) as e:
        warning(f"Could not calculate size of {path}: {e}")
    return total


def _format_size(size: int) -> str:
    """Format size in human-readable form."""
    if size < 1024:
        return f"{size}B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f}KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f}MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.1f}GB"
