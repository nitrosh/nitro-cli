"""Renderer for generating HTML from nitro-ui pages."""

import threading
from contextlib import contextmanager
from typing import Any, Optional, List
from pathlib import Path
import importlib.util
import sys

from ..core.page import Page
from ..utils import error, warning, error_panel

_import_lock = threading.RLock()


@contextmanager
def _project_import_context(project_root: Path, invalidate_pages):
    """Serialize all access to sys.path and sys.modules during page import.

    Python's import machinery touches global state. Holding the lock for the
    full import (path setup, module invalidation, exec_module, sys.modules
    insert/remove, path teardown) is what makes parallel page rendering
    correct; releasing it earlier opens windows where another thread can
    yank a path or shared module out from under an in-flight import.
    """
    paths_to_remove = []
    with _import_lock:
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
            paths_to_remove.append(str(project_root))

        src_dir = project_root / "src"
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))
            paths_to_remove.append(str(src_dir))

        invalidate_pages(project_root)

        try:
            yield
        finally:
            for path in paths_to_remove:
                if path in sys.path:
                    sys.path.remove(path)


class Renderer:
    """Handles rendering of nitro-ui pages to HTML."""

    def __init__(self, config: Any):
        self.config = config
        self.pretty_print = config.renderer.get("pretty_print", False)
        self.minify_html = config.renderer.get("minify_html", False)

    def is_dynamic_route(self, page_path: Path) -> bool:
        """Check if a page uses dynamic routing (e.g., [slug].py)."""
        return "[" in page_path.stem and "]" in page_path.stem

    def get_dynamic_paths(self, page_path: Path, project_root: Path) -> List[dict]:
        """Get all paths for a dynamic route.

        Args:
            page_path: Path to dynamic page file
            project_root: Project root directory

        Returns:
            List of parameter dictionaries from get_paths()
        """
        try:
            with _project_import_context(project_root, self._invalidate_project_modules):
                module_name = f"dynamic_paths_{page_path.stem}_{id(self)}_{threading.get_ident()}"
                spec = importlib.util.spec_from_file_location(module_name, page_path)

                if not spec or not spec.loader:
                    return []

                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module

                try:
                    spec.loader.exec_module(module)

                    if not hasattr(module, "get_paths"):
                        return []

                    paths = module.get_paths()
                    result = []
                    for path_params in paths:
                        if isinstance(path_params, dict):
                            result.append(path_params)
                        else:
                            param_name = page_path.stem[1:-1]
                            result.append({param_name: path_params})
                    return result

                finally:
                    if spec.name in sys.modules:
                        del sys.modules[spec.name]

        except Exception:
            return []

    def render_dynamic_page_single(
        self, page_path: Path, project_root: Path, params: dict
    ) -> Optional[str]:
        """Render a single instance of a dynamic page with given params.

        Args:
            page_path: Path to dynamic page file
            project_root: Project root directory
            params: Parameters to pass to render()

        Returns:
            Rendered HTML or None on error
        """
        html = None
        try:
            with _project_import_context(project_root, self._invalidate_project_modules):
                module_name = (
                    f"dynamic_single_{page_path.stem}_{id(self)}_{threading.get_ident()}"
                )
                spec = importlib.util.spec_from_file_location(module_name, page_path)

                if not spec or not spec.loader:
                    return None

                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module

                try:
                    spec.loader.exec_module(module)

                    if not hasattr(module, "render"):
                        return None

                    page = module.render(**params)

                    if isinstance(page, Page):
                        html = self._render_page_object(page)
                    else:
                        html = self._render_element(page)

                finally:
                    if spec.name in sys.modules:
                        del sys.modules[spec.name]

        except Exception:
            return None

        if html:
            html = self._post_process(html)

        return html

    def render_dynamic_page(
        self,
        page_path: Path,
        project_root: Path,
    ) -> List[tuple]:
        """Render a dynamic page for all its paths."""
        results = []

        try:
            with _project_import_context(project_root, self._invalidate_project_modules):
                module_name = (
                    f"dynamic_page_{page_path.stem}_{id(self)}_{threading.get_ident()}"
                )
                spec = importlib.util.spec_from_file_location(module_name, page_path)

                if not spec or not spec.loader:
                    error(f"Failed to load dynamic page: {page_path}")
                    return results

                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module

                try:
                    spec.loader.exec_module(module)

                    if not hasattr(module, "get_paths"):
                        error(f"Dynamic page {page_path} missing get_paths() function")
                        return results

                    if not hasattr(module, "render"):
                        error(f"Dynamic page {page_path} missing render() function")
                        return results

                    paths = module.get_paths()

                    for path_params in paths:
                        try:
                            if isinstance(path_params, dict):
                                page = module.render(**path_params)
                            else:
                                page = module.render(path_params)

                            if isinstance(page, Page):
                                html = self._render_page_object(page)
                            else:
                                html = self._render_element(page)

                            if html:
                                html = self._post_process(html)

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

        return results

    def _get_dynamic_output_name(self, page_path: Path, params: Any) -> str:
        """Get the output filename for a dynamic page."""
        import re

        stem = page_path.stem

        if isinstance(params, dict):
            output_name = stem
            for key, value in params.items():
                output_name = output_name.replace(f"[{key}]", str(value))
        else:
            output_name = re.sub(r"\[\w+\]", str(params), stem)

        return f"{output_name}.html"

    def render_page(
        self, page_path: Path, project_root: Path, return_page: bool = False
    ) -> Optional[Any]:
        """Render a page file to HTML.

        Args:
            page_path: Path to page file
            project_root: Project root directory
            return_page: If True, return the Page object instead of rendered HTML

        Returns:
            HTML string, Page object (if return_page=True), or None on error
        """
        try:
            with _project_import_context(project_root, self._invalidate_project_modules):
                module_name = f"page_{page_path.stem}_{id(self)}_{threading.get_ident()}"
                spec = importlib.util.spec_from_file_location(module_name, page_path)

                if not spec or not spec.loader:
                    error(f"Failed to load page: {page_path}")
                    return None

                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module

                try:
                    spec.loader.exec_module(module)

                    if not hasattr(module, "render"):
                        error(f"Page {page_path} missing render() function")
                        return None

                    page = module.render()

                    if return_page:
                        return page

                    if isinstance(page, Page):
                        html = self._render_page_object(page)
                    else:
                        html = self._render_element(page)

                    if html:
                        html = self._post_process(html)

                    return html

                finally:
                    if spec.name in sys.modules:
                        del sys.modules[spec.name]

        except SyntaxError as e:
            error_panel(
                "Syntax Error",
                str(e.msg) if hasattr(e, "msg") else str(e),
                file_path=str(e.filename) if e.filename else str(page_path),
                line=e.lineno or 1,
                hint="Check for missing parentheses, quotes, or colons",
            )
            return None

        except NameError as e:
            import traceback

            tb = traceback.extract_tb(e.__traceback__)
            if tb:
                last_frame = tb[-1]
                suggestion = self._suggest_name_fix(str(e))
                error_panel(
                    "Name Error",
                    str(e),
                    file_path=last_frame.filename,
                    line=last_frame.lineno,
                    hint=suggestion,
                )
            else:
                error(f"NameError in {page_path}: {e}")
            return None

        except ImportError as e:
            import traceback

            tb = traceback.extract_tb(e.__traceback__)
            frame = tb[-1] if tb else None
            error_panel(
                "Import Error",
                str(e),
                file_path=frame.filename if frame else str(page_path),
                line=frame.lineno if frame else 1,
                hint="Check that the module is installed and the import path is correct",
            )
            return None

        except AttributeError as e:
            import traceback

            tb = traceback.extract_tb(e.__traceback__)
            if tb:
                last_frame = tb[-1]
                error_panel(
                    "Attribute Error",
                    str(e),
                    file_path=last_frame.filename,
                    line=last_frame.lineno,
                    hint="Check that the object has the attribute you're trying to access",
                )
            else:
                error(f"AttributeError in {page_path}: {e}")
            return None

        except Exception as e:
            import traceback

            tb = traceback.extract_tb(e.__traceback__)

            relevant_frame = None
            page_path_str = str(page_path)
            for frame in reversed(tb):
                if page_path_str in frame.filename:
                    relevant_frame = frame
                    break

            if relevant_frame is None and tb:
                relevant_frame = tb[-1]

            if relevant_frame:
                error_panel(
                    type(e).__name__,
                    str(e),
                    file_path=relevant_frame.filename,
                    line=relevant_frame.lineno,
                )
            else:
                error(f"Error rendering {page_path}: {e}")
            return None

    def _suggest_name_fix(self, error_msg: str) -> Optional[str]:
        """Suggest fixes for common name errors."""
        import difflib

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
            "Paragraph",
            "Href",
            "Link",
            "Image",
            "Form",
            "Input",
            "Button",
            "Label",
            "Select",
            "Textarea",
            "Option",
            "Table",
            "TableRow",
            "TableDataCell",
            "TableHeaderCell",
            "UnorderedList",
            "OrderedList",
            "ListItem",
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
            "Config",
        ]

        if "name '" in error_msg and "' is not defined" in error_msg:
            start = error_msg.index("name '") + 6
            end = error_msg.index("' is not defined")
            undefined_name = error_msg[start:end]

            matches = difflib.get_close_matches(
                undefined_name, common_names, n=1, cutoff=0.6
            )
            if matches:
                return f"Did you mean '{matches[0]}'?"

        return "Check for typos in variable or function names"

    def _render_page_object(self, page: Page) -> str:
        """Render a Page object to HTML."""
        if hasattr(page.content, "render"):
            return page.content.render()
        return str(page.content)

    def _render_element(self, element: Any) -> str:
        """Render a nitro-ui element to HTML."""
        if hasattr(element, "render"):
            return element.render()
        return str(element)

    def _post_process(self, html: str) -> str:
        """Post-process HTML (minify or pretty print)."""
        if self.minify_html:
            try:
                import minify_html

                html = minify_html.minify(html, minify_css=True, minify_js=True)
            except ImportError:
                warning("minify-html not installed, skipping minification")

        elif self.pretty_print:
            try:
                from bs4 import BeautifulSoup

                try:
                    import html5lib  # noqa: F401

                    soup = BeautifulSoup(html, "html5lib")
                except ImportError:
                    warning(
                        "html5lib not installed, falling back to html.parser "
                        "(SVG attributes like viewBox may be lowercased). "
                        "Install with: pip install html5lib"
                    )
                    soup = BeautifulSoup(html, "html.parser")
                html = soup.prettify()
            except ImportError:
                warning(
                    "beautifulsoup4 not installed, skipping pretty print (pip install beautifulsoup4)"
                )

        return html

    def _invalidate_project_modules(self, project_root: Path) -> None:
        """Remove cached page modules to ensure fresh imports.

        Only invalidates modules under src/pages/ - shared modules like
        components, utils, etc. are kept cached. This prevents a race
        condition where one thread invalidates shared modules while another
        thread is mid-import during parallel page generation.
        """
        pages_dir = str(project_root / "src" / "pages")
        modules_to_remove = []

        for name, module in sys.modules.items():
            if module is None:
                continue
            module_file = getattr(module, "__file__", None)
            if module_file and pages_dir in module_file:
                modules_to_remove.append(name)

        for name in modules_to_remove:
            del sys.modules[name]

    def invalidate_all_src_modules(self, project_root: Path) -> None:
        """Drop every cached module whose file lives under src/.

        Used by dev mode so that edits to shared modules (components, utils,
        data loaders) are picked up without restarting the server. Build mode
        should keep using _invalidate_project_modules, which is page-only and
        safe for parallel generation.
        """
        src_dir = str(project_root / "src")
        modules_to_remove = []

        with _import_lock:
            for name, module in sys.modules.items():
                if module is None:
                    continue
                module_file = getattr(module, "__file__", None)
                if module_file and module_file.startswith(src_dir):
                    modules_to_remove.append(name)

            for name in modules_to_remove:
                del sys.modules[name]

    def get_output_path(
        self, page_path: Path, source_dir: Path, build_dir: Path
    ) -> Path:
        """Get output path for a page."""
        pages_dir = source_dir / "pages"
        relative = page_path.relative_to(pages_dir)
        html_name = relative.stem + ".html"

        if relative.parent != Path("."):
            return build_dir / relative.parent / html_name
        return build_dir / html_name
