"""About page."""

from nitro_ui import (
    HTML,
    Head,
    Body,
    Title,
    Meta,
    Link,
    Main,
    Div,
    H1,
    H2,
    Paragraph,
    UnorderedList,
    ListItem,
)
from nitro import Page, load_data
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from components.header import Header
from components.footer import Footer


def render():
    """Render the about page."""
    data = load_data("src/data/site.json")
    site_name = data.site.name

    content = Div(
        H1("About This Site"),
        Paragraph(
            "This is a static site built with Nitro CLI and nitro-ui. "
            "Everything you see is generated from Python code."
        ),
        H2("How It Works"),
        Paragraph(
            "Each page is a Python file in the src/pages/ directory. "
            "The file path determines the URL structure:"
        ),
        UnorderedList(
            ListItem("src/pages/index.py becomes /index.html"),
            ListItem("src/pages/about.py becomes /about.html"),
            ListItem("src/pages/blog/post.py becomes /blog/post.html"),
        ),
        H2("Project Structure"),
        UnorderedList(
            ListItem("src/pages/ - Your page files"),
            ListItem("src/components/ - Reusable components"),
            ListItem("src/styles/ - CSS stylesheets"),
            ListItem("src/data/ - JSON/YAML data files"),
            ListItem("build/ - Generated static files"),
        ),
        H2("Next Steps"),
        Paragraph(
            "Start by editing src/pages/index.py to customize your home page. "
            "Create new pages by adding .py files to src/pages/. "
            "Run nitro build when you're ready to deploy."
        ),
        class_name="about-content",
    )

    page = HTML(
        Head(
            Meta(charset="UTF-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title(f"About - {site_name}"),
            Link(rel="stylesheet", href="/assets/styles/main.css"),
        ),
        Body(
            Header(site_name),
            Main(content),
            Footer(),
        ),
    )

    return Page(
        title=f"About - {site_name}",
        meta={"description": f"About {site_name}"},
        content=page,
    )
