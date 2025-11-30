"""About page using nitro-ui."""

from nitro_ui import HTML, Head, Body, Title, Meta, Link, Div, H1, Paragraph
from nitro import Page
import sys
from pathlib import Path

# Add parent directory to path to import components
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.header import Header
from components.footer import Footer


def render():
    """Render the about page.

    Returns:
        Page object with HTML content
    """
    # Create content div
    content_div = Div(
        H1("About Me"),
        Paragraph(
            "This is the about page. Customize it to tell visitors about yourself and your work!"
        ),
        Paragraph(
            "You can add more pages by creating new Python files in src/pages/. "
            "The file path determines the URL - for example, src/pages/projects/my-project.py "
            "becomes /projects/my-project.html"
        ),
        class_name="content"
    )

    # Create container div
    container = Div(content_div, class_name="container")

    # Create page
    page = HTML(
        Head(
            Meta(charset="UTF-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title("About - My Portfolio"),
            Link(rel="stylesheet", href="/assets/styles/main.css"),
        ),
        Body(Header("My Portfolio"), container, Footer()),
    )

    return Page(
        title="About - My Portfolio",
        meta={
            "description": "About me and my work",
            "keywords": "about, nitro, portfolio",
        },
        content=page,
    )
