"""Welcome page - the default splash screen for new Nitro projects."""

import sys

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
    Paragraph,
    Href,
    Span,
    Code,
)
from nitro import Page

# Get version info
python_version = (
    f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
)

try:
    from nitro import __version__ as nitro_version
except ImportError:
    nitro_version = "1.0.0"


def render():
    """Render the welcome splash page."""

    # Status badge
    status = Div(
        Span(cls="status-dot"),
        "Server running",
        cls="status",
    )

    # Next steps card
    next_steps = Div(
        H2("Next Steps", cls="card-title"),
        Div(
            Div(
                Span("1", cls="command-icon"),
                Div(
                    Code("src/pages/index.py", cls="command-code"),
                    Paragraph(
                        "Edit this file to customize your home page",
                        cls="command-desc",
                    ),
                    cls="command-text",
                ),
                cls="command",
            ),
            Div(
                Span("2", cls="command-icon"),
                Div(
                    Code("src/components/", cls="command-code"),
                    Paragraph("Create reusable components", cls="command-desc"),
                    cls="command-text",
                ),
                cls="command",
            ),
            Div(
                Span("3", cls="command-icon"),
                Div(
                    Code("nitro build", cls="command-code"),
                    Paragraph("Build for production when ready", cls="command-desc"),
                    cls="command-text",
                ),
                cls="command",
            ),
        ),
        cls="card",
    )

    # System info card
    system_info = Div(
        H2("Environment", cls="card-title"),
        Div(
            Div(
                Paragraph("Python", cls="info-label"),
                Paragraph(python_version, cls="info-value"),
                cls="info-item",
            ),
            Div(
                Paragraph("Nitro CLI", cls="info-label"),
                Paragraph(f"v{nitro_version}", cls="info-value"),
                cls="info-item",
            ),
            cls="info-grid",
        ),
        cls="card",
    )

    # Links
    links = Div(
        Href(
            "Documentation",
            href="https://github.com/nitrosh/nitro-cli",
            target="_blank",
        ),
        Href("nitro-ui", href="https://github.com/nitrosh/nitro-ui", target="_blank"),
        Href(
            "Examples",
            href="https://github.com/nitrosh/nitro-cli/tree/main/examples",
            target="_blank",
        ),
        cls="links",
    )

    # Footer hint
    footer = Paragraph(
        "Edit ",
        Code("src/pages/index.py"),
        " to replace this page",
        cls="footer",
    )

    page = HTML(
        Head(
            Meta(charset="UTF-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title("Welcome to Nitro"),
            Meta(name="description", content="Your new Nitro project is ready"),
            Link(rel="stylesheet", href="/styles/main.css"),
        ),
        Body(
            Main(
                Section(
                    Div("⚡", cls="logo"),
                    H1("Nitro", cls="brand"),
                    Paragraph("Your project is ready", cls="tagline"),
                    status,
                    next_steps,
                    system_info,
                    links,
                    footer,
                    cls="splash",
                ),
            ),
        ),
    )

    return Page(
        title="Welcome to Nitro",
        meta={"description": "Your new Nitro project is ready"},
        content=page,
    )
