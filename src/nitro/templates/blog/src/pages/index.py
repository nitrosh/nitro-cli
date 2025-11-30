"""Home page using nitro-ui."""

from nitro_ui import HTML, Head, Body, Title, Meta, Link, Div, H1, H2, Paragraph
from nitro import Page
import sys
from pathlib import Path

# Add parent directory to path to import components
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.header import Header
from components.footer import Footer


def render():
    """Render the home page.

    Returns:
        Page object with HTML content
    """
    # Create content div
    content_div = Div(
        H1("Welcome to My Blog!"),
        Paragraph(
            "This is a blog template for building static websites with Nitro CLI and nitro-ui."
        ),
        H2("Getting Started"),
        Paragraph(
            "Edit the files in src/pages/ to create your blog posts. "
            "Components are in src/components/ and can be reused across pages."
        ),
        H2("Features"),
        Paragraph("✓ Python-based HTML generation with nitro-ui"),
        Paragraph("✓ Component-based architecture"),
        Paragraph("✓ Hot reload development server"),
        Paragraph("✓ Production-ready builds"),
        Paragraph("✓ Data loading with nitro-datastore"),
        Paragraph("✓ Plugin system with nitro-dispatch"),
        class_name="content",
    )

    # Create container div
    container = Div(content_div, class_name="container")

    # Create page
    page = HTML(
        Head(
            Meta(charset="UTF-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title("Home - My Blog"),
            Link(rel="stylesheet", href="/assets/styles/main.css"),
        ),
        Body(Header("My Blog"), container, Footer()),
    )

    return Page(
        title="Home - My Blog",
        meta={
            "description": "Welcome to my blog built with Nitro and nitro-ui",
            "keywords": "nitro, blog, nitro-ui",
        },
        content=page,
    )
