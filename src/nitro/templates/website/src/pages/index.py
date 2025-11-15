"""Home page."""

from ydnatl import HTML, Head, Body, Title, Meta, Link, Div, H1, H2, Paragraph
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
        H1("Welcome to Nitro!"),
        Paragraph(
            "This is a starter template for building static websites with Nitro CLI and YDNATL."
        ),
        H2("Getting Started"),
        Paragraph(
            "Edit the files in src/pages/ to create your site. "
            "Components are in src/components/ and can be reused across pages."
        ),
        H2("Features"),
        Paragraph("✓ Python-based HTML generation with YDNATL"),
        Paragraph("✓ Component-based architecture"),
        Paragraph("✓ Hot reload development server"),
        Paragraph("✓ Production-ready builds"),
    )
    content_div.add_attribute("class", "content")

    # Create container div
    container = Div(content_div)
    container.add_attribute("class", "container")

    # Create page
    page = HTML(
        Head(
            Meta(charset="UTF-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title("Home - My Website"),
            Link(rel="stylesheet", href="/assets/styles/main.css"),
        ),
        Body(Header("My Website"), container, Footer()),
    )

    return Page(
        title="Home - My Website",
        meta={
            "description": "Welcome to my website built with Nitro and YDNATL",
            "keywords": "nitro, static site, ydnatl",
        },
        content=page,
    )
