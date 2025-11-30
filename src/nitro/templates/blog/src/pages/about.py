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
        H1("About"),
        Paragraph(
            "This is the about page. Customize it to tell visitors about your blog!"
        ),
        Paragraph(
            "You can add more pages by creating new Python files in src/pages/. "
            "The file path determines the URL - for example, src/pages/posts/my-post.py "
            "becomes /posts/my-post.html"
        ),
        class_name="content",
    )

    # Create container div
    container = Div(content_div, class_name="container")

    # Create page
    page = HTML(
        Head(
            Meta(charset="UTF-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title("About - My Blog"),
            Link(rel="stylesheet", href="/assets/styles/main.css"),
        ),
        Body(Header("My Blog"), container, Footer()),
    )

    return Page(
        title="About - My Blog",
        meta={"description": "About my blog", "keywords": "about, nitro, blog"},
        content=page,
    )
