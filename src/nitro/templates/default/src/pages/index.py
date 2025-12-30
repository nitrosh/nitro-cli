"""Home page - your starting point."""

from nitro_ui import (
    HTML,
    Head,
    Body,
    Title,
    Meta,
    Link,
    Main,
    Section,
    Div,
    H1,
    H2,
    H3,
    Paragraph,
    Href,
    Span,
    Code,
    Pre,
)
from nitro import Page
from nitro_datastore import NitroDataStore
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from components.header import Header
from components.footer import Footer


def render():
    """Render the home page."""
    data = NitroDataStore.from_file("src/data/site.json")
    site_name = data.site.name
    site_tagline = data.site.tagline

    # Hero Section
    hero = Section(
        Div(
            H1(site_name, class_name="hero-title"),
            Paragraph(site_tagline, class_name="hero-tagline"),
            Div(
                Href("Get Started", href="#quickstart", class_name="btn btn-primary"),
                Href("Learn More", href="/about.html", class_name="btn btn-secondary"),
                class_name="hero-actions",
            ),
            class_name="hero-content",
        ),
        class_name="hero",
    )

    # Quick Start Section
    quickstart = Section(
        H2("Quick Start", class_name="section-title"),
        Div(
            Div(
                Span("1", class_name="step-number"),
                H3("Edit Your Pages"),
                Paragraph(
                    "Open ",
                    Code("src/pages/index.py"),
                    " and start customizing. Each file becomes a page on your site.",
                ),
                class_name="step-card",
            ),
            Div(
                Span("2", class_name="step-number"),
                H3("Create Components"),
                Paragraph(
                    "Build reusable components in ",
                    Code("src/components/"),
                    " and import them into any page.",
                ),
                class_name="step-card",
            ),
            Div(
                Span("3", class_name="step-number"),
                H3("Add Your Styles"),
                Paragraph(
                    "Customize the look in ",
                    Code("src/styles/main.css"),
                    " or add new stylesheets.",
                ),
                class_name="step-card",
            ),
            class_name="steps-grid",
        ),
        id="quickstart",
        class_name="section",
    )

    # Features Section
    features = Section(
        H2("What You Can Do", class_name="section-title"),
        Div(
            Div(
                Span("lightning", class_name="feature-icon"),
                H3("Fast Development"),
                Paragraph(
                    "Hot reload server updates your browser instantly as you code."
                ),
                class_name="feature-card",
            ),
            Div(
                Span("code", class_name="feature-icon"),
                H3("Pure Python"),
                Paragraph(
                    "No template languages to learn. Write HTML with Python functions."
                ),
                class_name="feature-card",
            ),
            Div(
                Span("package", class_name="feature-icon"),
                H3("Zero Config"),
                Paragraph("Sensible defaults that just work. Customize when you need."),
                class_name="feature-card",
            ),
            Div(
                Span("globe", class_name="feature-icon"),
                H3("Deploy Anywhere"),
                Paragraph(
                    "Static output works with any hosting: Netlify, Vercel, or your own server."
                ),
                class_name="feature-card",
            ),
            class_name="features-grid",
        ),
        class_name="section",
    )

    # Code Example Section
    code_example = Section(
        H2("How It Works", class_name="section-title"),
        Div(
            Pre(
                Code(
                    """from nitro_ui import HTML, Head, Body, H1

def render():
    return HTML(
        Head(Title("My Page")),
        Body(H1("Hello, World!"))
    )""",
                    class_name="language-python",
                ),
                class_name="code-block",
            ),
            Paragraph(
                "Each page is a Python file with a ",
                Code("render()"),
                " function that returns HTML elements.",
                class_name="code-caption",
            ),
            class_name="code-example",
        ),
        class_name="section section-alt",
    )

    # CTA Section
    cta = Section(
        Div(
            H2("Ready to build something amazing?"),
            Paragraph("Start editing this template and make it your own."),
            Href(
                "Read the Docs",
                href="https://github.com/nitro-sh/nitro-cli",
                target="_blank",
                class_name="btn btn-primary",
            ),
            class_name="cta-content",
        ),
        class_name="section cta",
    )

    page = HTML(
        Head(
            Meta(charset="UTF-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title(f"{site_name} - {site_tagline}"),
            Meta(name="description", content=site_tagline),
            Link(rel="stylesheet", href="/assets/styles/main.css"),
        ),
        Body(
            Header(site_name),
            Main(hero, quickstart, features, code_example, cta),
            Footer(),
        ),
    )

    return Page(
        title=f"{site_name} - {site_tagline}",
        meta={"description": site_tagline},
        content=page,
    )
