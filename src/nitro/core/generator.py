"""Generator for building static sites."""

from typing import List, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil
import os

from ..core.config import Config, load_config
from ..core.renderer import Renderer
from ..core.page import get_project_root
from ..core.cache import BuildCache
from ..plugins import PluginLoader
from ..utils import success, error, info, warning, console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
    MofNCompleteColumn,
)


class Generator:
    """Handles site generation pipeline."""

    def __init__(self, project_root: Optional[Path] = None, use_cache: bool = True):
        """Initialize generator.

        Args:
            project_root: Root directory of project (auto-detected if None)
            use_cache: Enable build cache for incremental builds
        """
        self.project_root = project_root or get_project_root() or Path.cwd()
        self.config = self._load_config()
        self.renderer = Renderer(self.config)
        self.source_dir = self.project_root / self.config.source_dir
        self.build_dir = self.project_root / self.config.build_dir
        self.plugin_loader = self._load_plugins()
        self.use_cache = use_cache
        self.cache = BuildCache(self.project_root) if use_cache else None

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

    def generate(
        self,
        verbose: bool = False,
        force: bool = False,
        parallel: bool = True,
        quiet: bool = False,
        production: bool = False,
    ) -> bool:
        """Generate the static site.

        Args:
            verbose: Enable verbose output
            force: Force full rebuild, ignore cache
            parallel: Use parallel page generation (default: True)
            quiet: Suppress progress output (for background thread execution)
            production: If True, exclude draft pages from output

        Returns:
            True if successful, False otherwise
        """
        self.production = production
        self.page_metadata = {}  # Store page metadata for sitemap
        info(f"Generating site from {self.source_dir}")
        info(f"Output directory: {self.build_dir}")

        # Check if config changed (forces full rebuild)
        config_path = self.project_root / "nitro.config.py"
        config_changed = False
        if self.cache and config_path.exists():
            config_changed = self.cache.is_config_changed(config_path)
            if config_changed:
                warning("Config changed, forcing full rebuild")
                force = True
            self.cache.update_config_hash(config_path)

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
        all_pages = self._find_pages()

        if not all_pages:
            error("No pages found in src/pages/")
            return False

        # Separate static and dynamic pages
        static_pages = []
        dynamic_pages = []
        for page in all_pages:
            if self.renderer.is_dynamic_route(page):
                dynamic_pages.append(page)
            else:
                static_pages.append(page)

        # Determine which static pages need to be rebuilt
        if self.cache and not force:
            components_dir = self.source_dir / "components"
            data_dir = self.source_dir / "data"
            pages_to_build = self.cache.get_changed_pages(
                static_pages, components_dir, data_dir
            )

            if not pages_to_build and not dynamic_pages:
                success("All pages are up to date (nothing to build)")
                return True

            skipped = len(static_pages) - len(pages_to_build)
            if skipped > 0:
                info(
                    f"Found {len(static_pages)} static page(s), {skipped} unchanged (cached)"
                )
            if pages_to_build:
                info(f"Building {len(pages_to_build)} static page(s)")
        else:
            pages_to_build = static_pages
            info(f"Found {len(static_pages)} static page(s) to generate")

        if dynamic_pages:
            info(f"Found {len(dynamic_pages)} dynamic route(s)")

        # Generate pages
        success_count = 0
        failed_pages = []

        # Use parallel generation for multiple pages
        use_parallel = parallel and len(pages_to_build) > 1
        max_workers = min(os.cpu_count() or 4, len(pages_to_build), 8)

        # Generate pages - with or without progress display
        if quiet:
            # Quiet mode: no progress bar (for background thread execution)
            success_count, failed_pages = self._generate_pages_quiet(
                pages_to_build, use_parallel, max_workers, verbose
            )
        else:
            # Normal mode: show progress bar
            success_count, failed_pages = self._generate_pages_with_progress(
                pages_to_build, use_parallel, max_workers, verbose
            )

        # Show results for static pages
        if pages_to_build:
            if failed_pages:
                success(
                    f"Generated {success_count}/{len(pages_to_build)} static page(s)"
                )
                for failed in failed_pages:
                    error(f"  Failed: {failed.relative_to(self.project_root)}")
            else:
                success(f"Generated {success_count} static page(s)")

        # Generate dynamic pages
        dynamic_count = 0
        if dynamic_pages:
            console.print("\n[dim]─── Generating Dynamic Routes [/dim]")
            for dynamic_page in dynamic_pages:
                relative_path = dynamic_page.relative_to(self.project_root)
                info(f"Processing dynamic route: {relative_path}")

                results = self.renderer.render_dynamic_page(
                    dynamic_page, self.project_root
                )

                for output_name, html in results:
                    if html:
                        # Determine output directory based on page location
                        pages_dir = self.source_dir / "pages"
                        rel_dir = dynamic_page.parent.relative_to(pages_dir)
                        if str(rel_dir) == ".":
                            output_path = self.build_dir / output_name
                        else:
                            output_path = self.build_dir / rel_dir / output_name

                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        output_path.write_text(html)
                        dynamic_count += 1

                        if verbose:
                            console.print(
                                f"  → {output_path.relative_to(self.project_root)}"
                            )

            if dynamic_count > 0:
                success(f"Generated {dynamic_count} page(s) from dynamic routes")

        # Save the cache
        if self.cache:
            self.cache.save()

        # Copy assets
        self._copy_assets(verbose)

        success("Site generation complete!")
        return True

    def _generate_pages_quiet(
        self,
        pages_to_build: List[Path],
        use_parallel: bool,
        max_workers: int,
        verbose: bool,
    ) -> tuple:
        """Generate pages without progress display (for background threads).

        Args:
            pages_to_build: List of page paths to build
            use_parallel: Whether to use parallel generation
            max_workers: Max worker threads for parallel generation
            verbose: Enable verbose output

        Returns:
            Tuple of (success_count, failed_pages)
        """
        success_count = 0
        failed_pages = []

        if use_parallel and len(pages_to_build) >= 4:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_page = {
                    executor.submit(
                        self._render_single_page, page_path, verbose
                    ): page_path
                    for page_path in pages_to_build
                }

                for future in as_completed(future_to_page):
                    page_path = future_to_page[future]
                    try:
                        result = future.result()
                        if result:
                            success_count += 1
                            if self.cache:
                                self.cache.update_page_hash(page_path)
                        else:
                            failed_pages.append(page_path)
                    except Exception as e:
                        error(f"Error generating {page_path}: {e}")
                        failed_pages.append(page_path)
        else:
            for page_path in pages_to_build:
                if self._render_page_sequential(page_path, verbose):
                    success_count += 1
                    if self.cache:
                        self.cache.update_page_hash(page_path)
                else:
                    failed_pages.append(page_path)

        return success_count, failed_pages

    def _generate_pages_with_progress(
        self,
        pages_to_build: List[Path],
        use_parallel: bool,
        max_workers: int,
        verbose: bool,
    ) -> tuple:
        """Generate pages with progress display.

        Args:
            pages_to_build: List of page paths to build
            use_parallel: Whether to use parallel generation
            max_workers: Max worker threads for parallel generation
            verbose: Enable verbose output

        Returns:
            Tuple of (success_count, failed_pages)
        """
        success_count = 0
        failed_pages = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            transient=True,
        ) as progress:
            task = progress.add_task("Generating pages...", total=len(pages_to_build))

            if use_parallel and len(pages_to_build) >= 4:
                progress.update(
                    task,
                    description=f"Generating {len(pages_to_build)} pages ({max_workers} workers)",
                )

                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_page = {
                        executor.submit(
                            self._render_single_page, page_path, verbose
                        ): page_path
                        for page_path in pages_to_build
                    }

                    for future in as_completed(future_to_page):
                        page_path = future_to_page[future]
                        try:
                            result = future.result()
                            if result:
                                success_count += 1
                                if self.cache:
                                    self.cache.update_page_hash(page_path)
                            else:
                                failed_pages.append(page_path)
                        except Exception as e:
                            error(f"Error generating {page_path}: {e}")
                            failed_pages.append(page_path)

                        progress.update(task, advance=1)
            else:
                for page_path in pages_to_build:
                    relative_path = page_path.relative_to(self.project_root)
                    progress.update(task, description=str(relative_path))

                    if verbose:
                        console.print(f"  Processing: {relative_path}")

                    if self._render_page_sequential(page_path, verbose):
                        success_count += 1
                        if self.cache:
                            self.cache.update_page_hash(page_path)
                    else:
                        failed_pages.append(page_path)

                    progress.update(task, advance=1)

        return success_count, failed_pages

    def _render_page_sequential(self, page_path: Path, verbose: bool = False) -> bool:
        """Render a single page sequentially (with hooks and output).

        Args:
            page_path: Path to page file
            verbose: Enable verbose output

        Returns:
            True if successful, False otherwise
        """
        # Render with page object return to check draft status
        page_obj = self.renderer.render_page(
            page_path, self.project_root, return_page=True
        )

        if page_obj is None:
            return False

        # Check for draft status in production mode
        is_draft = (
            getattr(page_obj, "draft", False) if hasattr(page_obj, "draft") else False
        )
        if getattr(self, "production", False) and is_draft:
            if verbose:
                console.print(
                    f"    [dim]Skipping draft: {page_path.relative_to(self.project_root)}[/]"
                )
            return True  # Return True to not count as failure

        # Get HTML content
        if hasattr(page_obj, "content"):
            html = self.renderer._render_page_object(page_obj)
            html = self.renderer._post_process(html)
        else:
            html = self.renderer._render_element(page_obj)
            html = self.renderer._post_process(html)

        if html:
            hook_result = self.plugin_loader.trigger(
                "nitro.post_generate",
                {
                    "page_path": str(page_path),
                    "output": html,
                    "config": self.config,
                },
            )

            if (
                hook_result
                and isinstance(hook_result, dict)
                and "output" in hook_result
            ):
                html = hook_result["output"]

            output_path = self.renderer.get_output_path(
                page_path, self.source_dir, self.build_dir
            )

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html)

            # Store metadata for sitemap
            if hasattr(self, "page_metadata"):
                rel_path = str(output_path.relative_to(self.build_dir))
                meta = (
                    getattr(page_obj, "meta", {}) if hasattr(page_obj, "meta") else {}
                )
                self.page_metadata[rel_path] = {
                    "draft": is_draft,
                    **meta,
                }

            if verbose:
                console.print(f"    → {output_path.relative_to(self.project_root)}")

            return True

        return False

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

    def _render_single_page(self, page_path: Path, verbose: bool = False) -> bool:
        """Render a single page (for parallel execution).

        Args:
            page_path: Path to page file
            verbose: Enable verbose output

        Returns:
            True if successful, False otherwise
        """
        try:
            # Render with page object return to check draft status
            page_obj = self.renderer.render_page(
                page_path, self.project_root, return_page=True
            )

            if page_obj is None:
                return False

            # Check for draft status in production mode
            is_draft = (
                getattr(page_obj, "draft", False)
                if hasattr(page_obj, "draft")
                else False
            )
            if getattr(self, "production", False) and is_draft:
                return True  # Skip drafts in production but count as success

            # Get HTML content
            if hasattr(page_obj, "content"):
                html = self.renderer._render_page_object(page_obj)
                html = self.renderer._post_process(html)
            else:
                html = self.renderer._render_element(page_obj)
                html = self.renderer._post_process(html)

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

                # Ensure parent directory exists (thread-safe with exist_ok)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Write HTML file
                output_path.write_text(html)

                # Store metadata for sitemap
                if hasattr(self, "page_metadata"):
                    rel_path = str(output_path.relative_to(self.build_dir))
                    meta = (
                        getattr(page_obj, "meta", {})
                        if hasattr(page_obj, "meta")
                        else {}
                    )
                    self.page_metadata[rel_path] = {
                        "draft": is_draft,
                        **meta,
                    }

                if verbose:
                    console.print(f"  → {output_path.relative_to(self.project_root)}")

                return True

            return False
        except Exception as e:
            error(f"Error rendering {page_path}: {e}")
            return False

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

        # Copy public files (src/public/ -> build/)
        public_src = self.source_dir / "public"
        if public_src.exists():
            # Copy public files to root of build directory
            self._copy_directory(public_src, self.build_dir, "public", verbose)

        # Copy static files (static/ -> build/)
        static_src = self.project_root / "static"
        if static_src.exists():
            self._copy_directory(static_src, self.build_dir, "static", verbose)

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
                    console.print(f"  Copied: {relative}")

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
