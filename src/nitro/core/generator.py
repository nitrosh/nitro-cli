"""Generator for building static sites."""

from typing import List, Optional
from pathlib import Path
import shutil

from ..core.config import Config, load_config
from ..core.renderer import Renderer
from ..core.project import get_project_root
from ..plugins import PluginLoader
from ..utils import success, error, info, logger
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)


class Generator:
    """Handles site generation pipeline."""

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize generator.

        Args:
            project_root: Root directory of project (auto-detected if None)
        """
        self.project_root = project_root or get_project_root() or Path.cwd()
        self.config = self._load_config()
        self.renderer = Renderer(self.config)
        self.source_dir = self.project_root / self.config.source_dir
        self.build_dir = self.project_root / self.config.build_dir
        self.plugin_loader = self._load_plugins()

    def _load_config(self) -> Config:
        """Load project configuration.

        Returns:
            Configuration object
        """
        config_path = self.project_root / "nitro.config.py"
        if config_path.exists():
            return load_config(config_path)
        return Config()

    def _load_plugins(self) -> PluginLoader:
        """Load plugins from configuration.

        Returns:
            PluginLoader instance with loaded plugins
        """
        loader = PluginLoader(config={"project_root": str(self.project_root)})

        # Load plugins from config if specified
        if hasattr(self.config, "plugins") and self.config.plugins:
            loader.load_plugins(self.config.plugins, self.project_root)

        # Trigger init hook
        loader.trigger("nitro.init", {"config": self.config})

        return loader

    def generate(self, verbose: bool = False) -> bool:
        """Generate the static site.

        Args:
            verbose: Enable verbose output

        Returns:
            True if successful, False otherwise
        """
        info(f"Generating site from {self.source_dir}")
        info(f"Output directory: {self.build_dir}")

        # Trigger pre-generate hook
        self.plugin_loader.trigger(
            "nitro.pre_generate",
            {
                "config": self.config,
                "source_dir": str(self.source_dir),
                "build_dir": str(self.build_dir),
            },
        )

        # Ensure build directory exists
        self.build_dir.mkdir(parents=True, exist_ok=True)

        # Find all page files
        pages = self._find_pages()

        if not pages:
            error("No pages found in src/pages/")
            return False

        info(f"Found {len(pages)} page(s) to generate")

        # Generate pages
        success_count = 0
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
        ) as progress:
            task = progress.add_task("Generating pages...", total=len(pages))

            for page_path in pages:
                if verbose:
                    logger.print(
                        f"  Processing: {page_path.relative_to(self.project_root)}"
                    )

                html = self.renderer.render_page(page_path, self.project_root)

                if html:
                    # Trigger post-generate hook to allow HTML modification
                    hook_result = self.plugin_loader.trigger(
                        "nitro.post_generate",
                        {
                            "page_path": str(page_path),
                            "output": html,
                            "config": self.config,
                        },
                    )

                    # Use modified output if returned
                    if (
                        hook_result
                        and isinstance(hook_result, dict)
                        and "output" in hook_result
                    ):
                        html = hook_result["output"]

                    output_path = self.renderer.get_output_path(
                        page_path, self.source_dir, self.build_dir
                    )

                    # Ensure parent directory exists
                    output_path.parent.mkdir(parents=True, exist_ok=True)

                    # Write HTML file
                    output_path.write_text(html)
                    success_count += 1

                    if verbose:
                        logger.print(
                            f"    → {output_path.relative_to(self.project_root)}"
                        )

                progress.update(task, advance=1)

        success(f"Generated {success_count}/{len(pages)} page(s)")

        # Copy assets
        self._copy_assets(verbose)

        success("Site generation complete!")
        return True

    def _find_pages(self) -> List[Path]:
        """Find all page files.

        Returns:
            List of page file paths
        """
        pages_dir = self.source_dir / "pages"

        if not pages_dir.exists():
            return []

        # Find all .py files except __init__.py
        pages = []
        for py_file in pages_dir.rglob("*.py"):
            if py_file.name != "__init__.py":
                pages.append(py_file)

        return sorted(pages)

    def _copy_assets(self, verbose: bool = False) -> None:
        """Copy static assets to build directory.

        Args:
            verbose: Enable verbose output
        """
        info("Copying static assets...")

        # Copy styles
        styles_src = self.source_dir / "styles"
        if styles_src.exists():
            styles_dest = self.build_dir / "assets" / "styles"
            self._copy_directory(styles_src, styles_dest, "styles", verbose)

        # Copy public files
        public_src = self.source_dir / "public"
        if public_src.exists():
            # Copy public files to root of build directory
            self._copy_directory(public_src, self.build_dir, "public", verbose)

    def _copy_directory(
        self, src: Path, dest: Path, name: str, verbose: bool = False
    ) -> None:
        """Copy a directory recursively.

        Args:
            src: Source directory
            dest: Destination directory
            name: Name for logging
            verbose: Enable verbose output
        """
        if not src.exists():
            return

        dest.mkdir(parents=True, exist_ok=True)

        files_copied = 0
        for item in src.rglob("*"):
            if item.is_file():
                relative = item.relative_to(src)
                dest_file = dest / relative
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_file)
                files_copied += 1

                if verbose:
                    logger.print(f"  Copied: {relative}")

        if files_copied > 0:
            success(f"Copied {files_copied} {name} file(s)")

    def clean(self) -> None:
        """Clean the build directory."""
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
            info(f"Cleaned {self.build_dir}")

    def regenerate_page(self, page_path: Path, verbose: bool = False) -> bool:
        """Regenerate a single page.

        Args:
            page_path: Path to page file
            verbose: Enable verbose output

        Returns:
            True if successful, False otherwise
        """
        if verbose:
            info(f"Regenerating: {page_path.relative_to(self.project_root)}")

        html = self.renderer.render_page(page_path, self.project_root)

        if html:
            output_path = self.renderer.get_output_path(
                page_path, self.source_dir, self.build_dir
            )

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html)

            if verbose:
                success(f"  → {output_path.relative_to(self.project_root)}")

            return True

        return False
