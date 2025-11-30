"""Renderer for generating HTML from nitro-ui pages."""

from typing import Any, Optional, List
from pathlib import Path
import importlib.util
import sys

from ..core.project import Page
from ..utils import error, warning, logger


class Renderer:
    """Handles rendering of nitro-ui pages to HTML."""

    def __init__(self, config: Any):
        """Initialize renderer.

        Args:
            config: Nitro configuration object
        """
        self.config = config
        self.pretty_print = config.renderer.get("pretty_print", False)
        self.minify_html = config.renderer.get("minify_html", False)

    def is_dynamic_route(self, page_path: Path) -> bool:
        """Check if a page uses dynamic routing.

        Dynamic routes have [param] in their filename, e.g., [slug].py

        Args:
            page_path: Path to page file

        Returns:
            True if this is a dynamic route
        """
        return "[" in page_path.stem and "]" in page_path.stem

    def get_dynamic_params(self, page_path: Path) -> List[str]:
        """Extract parameter names from a dynamic route.

        Args:
            page_path: Path to page file (e.g., [slug].py or [category]/[slug].py)

        Returns:
            List of parameter names
        """
        import re

        params = re.findall(r"\[(\w+)\]", str(page_path))
        return params

    def render_dynamic_page(
        self,
        page_path: Path,
        project_root: Path,
    ) -> List[tuple]:
        """Render a dynamic page for all its paths.

        Args:
            page_path: Path to dynamic page file
            project_root: Root directory of the project

        Returns:
            List of (output_path, html) tuples
        """
        results = []
        paths_to_remove = []

        try:
            # Add project root to Python path
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
                paths_to_remove.append(str(project_root))

            # Add src directory to Python path
            src_dir = project_root / "src"
            if str(src_dir) not in sys.path:
                sys.path.insert(0, str(src_dir))
                paths_to_remove.append(str(src_dir))

            # Invalidate cached modules
            self._invalidate_project_modules(project_root)

            # Load the page module
            module_name = f"dynamic_page_{page_path.stem}_{id(self)}"
            spec = importlib.util.spec_from_file_location(module_name, page_path)

            if not spec or not spec.loader:
                error(f"Failed to load dynamic page: {page_path}")
                return results

            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module

            try:
                spec.loader.exec_module(module)

                # Check for get_paths function
                if not hasattr(module, "get_paths"):
                    error(f"Dynamic page {page_path} missing get_paths() function")
                    return results

                # Check for render function
                if not hasattr(module, "render"):
                    error(f"Dynamic page {page_path} missing render() function")
                    return results

                # Get all paths to generate
                paths = module.get_paths()

                for path_params in paths:
                    try:
                        # Call render with the params
                        if isinstance(path_params, dict):
                            page = module.render(**path_params)
                        else:
                            page = module.render(path_params)

                        # Render to HTML
                        if isinstance(page, Page):
                            html = self._render_page_object(page)
                        else:
                            html = self._render_element(page)

                        # Apply post-processing
                        if html:
                            html = self._post_process(html)

                        # Determine output path
                        output_name = self._get_dynamic_output_name(
                            page_path, path_params
                        )
                        results.append((output_name, html))

                    except Exception as e:
                        error(
                            f"Error rendering {page_path} with params {path_params}: {e}"
                        )

            finally:
                if spec.name in sys.modules:
                    del sys.modules[spec.name]

        except Exception as e:
            error(f"Error processing dynamic page {page_path}: {e}")

        finally:
            for path in paths_to_remove:
                if path in sys.path:
                    sys.path.remove(path)

        return results

    def _get_dynamic_output_name(self, page_path: Path, params: Any) -> str:
        """Get the output filename for a dynamic page.

        Args:
            page_path: Path to dynamic page file
            params: Parameters for this instance

        Returns:
            Output filename (e.g., "my-post.html")
        """
        import re

        # Get the filename pattern
        stem = page_path.stem  # e.g., "[slug]"

        # Replace [param] with actual values
        if isinstance(params, dict):
            output_name = stem
            for key, value in params.items():
                output_name = output_name.replace(f"[{key}]", str(value))
        else:
            # Single param - replace all brackets
            output_name = re.sub(r"\[\w+\]", str(params), stem)

        return f"{output_name}.html"

    def render_page(self, page_path: Path, project_root: Path) -> Optional[str]:
        """Render a page file to HTML.

        Args:
            page_path: Path to page Python file
            project_root: Root directory of the project

        Returns:
            Rendered HTML string or None if error
        """
        # Track paths we add to clean up after
        paths_to_remove = []

        try:
            # Add project root to Python path
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
                paths_to_remove.append(str(project_root))

            # Add src directory to Python path for component imports
            src_dir = project_root / "src"
            if str(src_dir) not in sys.path:
                sys.path.insert(0, str(src_dir))
                paths_to_remove.append(str(src_dir))

            # Invalidate cached modules from the project to ensure fresh imports
            self._invalidate_project_modules(project_root)

            # Load the page module with a unique name to avoid caching issues
            module_name = f"page_{page_path.stem}_{id(self)}"
            spec = importlib.util.spec_from_file_location(module_name, page_path)

            if not spec or not spec.loader:
                error(f"Failed to load page: {page_path}")
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module

            try:
                spec.loader.exec_module(module)

                # Check if module has render function
                if not hasattr(module, "render"):
                    error(f"Page {page_path} missing render() function")
                    return None

                # Call render function
                page = module.render()

                # Handle Page object
                if isinstance(page, Page):
                    html = self._render_page_object(page)
                else:
                    # Assume it's a nitro-ui element
                    html = self._render_element(page)

                # Apply post-processing
                if html:
                    html = self._post_process(html)

                return html

            finally:
                # Clean up the dynamically loaded module to prevent memory leaks
                if spec.name in sys.modules:
                    del sys.modules[spec.name]

        except SyntaxError as e:
            # Handle syntax errors with precise location
            logger.code_error(
                title="Syntax Error",
                message=str(e.msg) if hasattr(e, "msg") else str(e),
                file_path=str(e.filename) if e.filename else str(page_path),
                line=e.lineno or 1,
                column=e.offset,
                suggestion="Check for missing parentheses, quotes, or colons",
            )
            return None

        except NameError as e:
            # Handle name errors with suggestions
            import traceback

            tb = traceback.extract_tb(e.__traceback__)
            if tb:
                last_frame = tb[-1]
                # Try to suggest similar names
                suggestion = self._suggest_name_fix(str(e))
                logger.code_error(
                    title="Name Error",
                    message=str(e),
                    file_path=last_frame.filename,
                    line=last_frame.lineno,
                    suggestion=suggestion,
                )
            else:
                error(f"NameError in {page_path}: {e}")
            return None

        except ImportError as e:
            # Handle import errors
            import traceback

            tb = traceback.extract_tb(e.__traceback__)
            frame = tb[-1] if tb else None
            logger.code_error(
                title="Import Error",
                message=str(e),
                file_path=frame.filename if frame else str(page_path),
                line=frame.lineno if frame else 1,
                suggestion="Check that the module is installed and the import path is correct",
            )
            return None

        except AttributeError as e:
            # Handle attribute errors
            import traceback

            tb = traceback.extract_tb(e.__traceback__)
            if tb:
                last_frame = tb[-1]
                logger.code_error(
                    title="Attribute Error",
                    message=str(e),
                    file_path=last_frame.filename,
                    line=last_frame.lineno,
                    suggestion="Check that the object has the attribute you're trying to access",
                )
            else:
                error(f"AttributeError in {page_path}: {e}")
            return None

        except Exception as e:
            # Generic error handling with traceback extraction
            import traceback

            tb = traceback.extract_tb(e.__traceback__)

            # Find the most relevant frame (prefer frames in the page file)
            relevant_frame = None
            page_path_str = str(page_path)
            for frame in reversed(tb):
                if page_path_str in frame.filename:
                    relevant_frame = frame
                    break

            if relevant_frame is None and tb:
                relevant_frame = tb[-1]

            if relevant_frame:
                logger.code_error(
                    title=type(e).__name__,
                    message=str(e),
                    file_path=relevant_frame.filename,
                    line=relevant_frame.lineno,
                )
            else:
                error(f"Error rendering {page_path}: {e}")
                traceback.print_exc()
            return None

        finally:
            # Clean up sys.path to avoid pollution
            for path in paths_to_remove:
                if path in sys.path:
                    sys.path.remove(path)

    def _suggest_name_fix(self, error_msg: str) -> Optional[str]:
        """Suggest fixes for common name errors.

        Args:
            error_msg: The error message

        Returns:
            Suggestion string or None
        """
        import difflib

        # Common nitro-ui elements
        common_names = [
            "HTML",
            "Head",
            "Body",
            "Div",
            "Span",
            "H1",
            "H2",
            "H3",
            "H4",
            "H5",
            "H6",
            "P",
            "Paragraph",
            "A",
            "Link",
            "Img",
            "Form",
            "Input",
            "Button",
            "Label",
            "Select",
            "Textarea",
            "Option",
            "Table",
            "Tr",
            "Td",
            "Th",
            "Ul",
            "Ol",
            "Li",
            "Nav",
            "Header",
            "Footer",
            "Section",
            "Article",
            "Main",
            "Aside",
            "Title",
            "Meta",
            "Script",
            "Style",
            "Strong",
            "Em",
            "Fragment",
            "Page",
            "load_data",
            "Config",
        ]

        # Extract the undefined name from the error message
        if "name '" in error_msg and "' is not defined" in error_msg:
            start = error_msg.index("name '") + 6
            end = error_msg.index("' is not defined")
            undefined_name = error_msg[start:end]

            # Find similar names
            matches = difflib.get_close_matches(
                undefined_name, common_names, n=1, cutoff=0.6
            )
            if matches:
                return f"Did you mean '{matches[0]}'?"

        return "Check for typos in variable or function names"

    def _render_page_object(self, page: Page) -> str:
        """Render a Page object to HTML.

        Args:
            page: Page object

        Returns:
            HTML string
        """
        # Check if content has render method (nitro-ui element)
        if hasattr(page.content, "render"):
            return page.content.render()

        # Otherwise, just convert to string
        return str(page.content)

    def _render_element(self, element: Any) -> str:
        """Render a nitro-ui element to HTML.

        Args:
            element: nitro-ui element

        Returns:
            HTML string
        """
        if hasattr(element, "render"):
            return element.render()
        return str(element)

    def _post_process(self, html: str) -> str:
        """Post-process HTML (minify, pretty print, etc.).

        Args:
            html: HTML string

        Returns:
            Processed HTML string
        """
        # Minification
        if self.minify_html:
            try:
                import htmlmin

                html = htmlmin.minify(html, remove_empty_space=True)
            except ImportError:
                warning("htmlmin not installed, skipping minification")

        # Pretty printing (if not minified)
        elif self.pretty_print:
            try:
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(html, "html.parser")
                html = soup.prettify()
            except ImportError:
                # Pretty print not available, return as-is
                pass

        return html

    def _invalidate_project_modules(self, project_root: Path) -> None:
        """Remove cached modules from project directory to ensure fresh imports.

        Args:
            project_root: Root directory of the project
        """
        project_str = str(project_root)
        modules_to_remove = []

        for name, module in sys.modules.items():
            if module is None:
                continue
            # Check if module has a file path within the project
            module_file = getattr(module, "__file__", None)
            if module_file and project_str in module_file:
                modules_to_remove.append(name)

        for name in modules_to_remove:
            del sys.modules[name]

    def get_output_path(
        self, page_path: Path, source_dir: Path, build_dir: Path
    ) -> Path:
        """Get output path for a page.

        Args:
            page_path: Path to source page file
            source_dir: Source directory (src/pages/)
            build_dir: Build output directory

        Returns:
            Output HTML file path
        """
        # Get relative path from pages directory
        pages_dir = source_dir / "pages"
        relative = page_path.relative_to(pages_dir)

        # Change extension to .html
        html_name = relative.stem + ".html"

        # Handle nested paths
        if relative.parent != Path("."):
            output_path = build_dir / relative.parent / html_name
        else:
            output_path = build_dir / html_name

        return output_path
