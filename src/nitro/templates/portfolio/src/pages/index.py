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
        H1("Welcome to My Portfolio!"),
        Paragraph(
            "This is a portfolio template for showcasing your work with Nitro CLI and nitro-ui."
        ),
        H2("Getting Started"),
        Paragraph(
            "Edit the files in src/pages/ to add your projects. "
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
            Title("Home - My Portfolio"),
            Link(rel="stylesheet", href="/assets/styles/main.css"),
        ),
        Body(Header("My Portfolio"), container, Footer()),
    )

    return Page(
        title="Home - My Portfolio",
        meta={
            "description": "Welcome to my portfolio built with Nitro and nitro-ui",
            "keywords": "nitro, portfolio, nitro-ui",
        },
        content=page,
    )
