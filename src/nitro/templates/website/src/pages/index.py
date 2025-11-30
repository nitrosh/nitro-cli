"""Home page using nitro-ui and nitro-datastore."""

from nitro_ui import (
    HTML,
    Head,
    Body,
    Title,
    Meta,
    Link,
    Div,
    H1,
    H2,
    Paragraph,
    Ul,
    Li,
)
from nitro import Page, load_data
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
    # Load site data using nitro-datastore
    data = load_data("src/data/site.json")

    # Access data using dot notation or path-based access
    site_name = data.site.name
    site_description = data.site.description

    # Build feature list from data
    feature_items = []
    for feature in data.features:
        item = Li(f"{feature['name']}: {feature['description']}")
        feature_items.append(item)

    features_list = Ul(*feature_items, class_name="feature-list")

    # Create content div
    content_div = Div(
        H1(f"Welcome to {site_name}!"),
        Paragraph(site_description),
        H2("Getting Started"),
        Paragraph(
            "Edit the files in src/pages/ to create your site. "
            "Components are in src/components/ and can be reused across pages."
        ),
        H2("Features"),
        features_list,
        class_name="content",
    )

    # Create container div
    container = Div(content_div, class_name="container")

    # Create page
    page = HTML(
        Head(
            Meta(charset="UTF-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title(f"Home - {site_name}"),
            Link(rel="stylesheet", href="/assets/styles/main.css"),
        ),
        Body(Header(site_name), container, Footer()),
    )

    return Page(
        title=f"Home - {site_name}",
        meta={
            "description": site_description,
            "keywords": "nitro, static site, nitro-ui",
        },
        content=page,
    )
