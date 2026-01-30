"""Export command for creating deployable archives."""

import click
import zipfile
from datetime import datetime
from pathlib import Path

from ..core.page import get_project_root
from ..core.config import load_config
from ..core.generator import Generator
from ..utils import success, error, info, warning


@click.command(name="export")
@click.option("--output", "-o", help="Output zip file path")
@click.option("--build-first", "-b", is_flag=True, help="Build before exporting")
def export_cmd(output, build_first):
    """Export the built site as a zip file."""
    project_root = get_project_root()

    if not project_root:
        error("Not in a Nitro project directory")
        return

    # Load config for site name
    config_path = project_root / "nitro.config.py"
    config = load_config(config_path) if config_path.exists() else None
    site_name = (
        getattr(config, "title", project_root.name) if config else project_root.name
    )
    # Sanitize site name for filename
    site_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in site_name)

    build_dir = project_root / (config.build_dir if config else "build")

    # Build if requested or if build directory doesn't exist
    if build_first or not build_dir.exists():
        if not build_dir.exists():
            info("Build directory not found, building first...")
        else:
            info("Building site...")

        generator = Generator(project_root)
        if not generator.generate():
            error("Build failed, cannot export")
            return

    # Check build directory exists and has files
    if not build_dir.exists():
        error(f"Build directory not found: {build_dir}")
        info("Run 'nitro build' first or use --build-first")
        return

    build_files = list(build_dir.rglob("*"))
    if not any(f.is_file() for f in build_files):
        error("Build directory is empty")
        return

    # Determine output path
    if output:
        output_path = Path(output)
        if not output_path.suffix:
            output_path = output_path.with_suffix(".zip")
    else:
        date_str = datetime.now().strftime("%Y%m%d")
        output_path = project_root / f"{site_name}-{date_str}.zip"

    # Create zip file
    file_count = 0
    total_size = 0

    try:
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in build_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(build_dir)
                    zf.write(file_path, arcname)
                    file_count += 1
                    total_size += file_path.stat().st_size

        zip_size = output_path.stat().st_size

        # Format sizes
        if total_size < 1024 * 1024:
            orig_size_str = f"{total_size / 1024:.1f}KB"
        else:
            orig_size_str = f"{total_size / (1024 * 1024):.1f}MB"

        if zip_size < 1024 * 1024:
            zip_size_str = f"{zip_size / 1024:.1f}KB"
        else:
            zip_size_str = f"{zip_size / (1024 * 1024):.1f}MB"

        compression_ratio = (1 - zip_size / total_size) * 100 if total_size > 0 else 0

        success(f"Exported {file_count} files to {output_path.name}")
        info(
            f"  Original: {orig_size_str}, Compressed: {zip_size_str} ({compression_ratio:.0f}% smaller)"
        )

    except Exception as e:
        error(f"Failed to create zip file: {e}")
