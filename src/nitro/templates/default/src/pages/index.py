"""Welcome page - the default splash screen for new Nitro projects."""

import sys

from nitro_ui.html import (
    html,
    head,
    body,
    title,
    meta,
    link,
    main,
    section,
    div,
    h1,
    h2,
    p,
    a,
    span,
    code,
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
    status = div(
        span(class_name="status-dot"),
        "Server running",
        class_name="status",
    )

    # Next steps card
    next_steps = div(
        h2("Next Steps", class_name="card-title"),
        div(
            div(
                span("1", class_name="command-icon"),
                div(
                    code("src/pages/index.py", class_name="command-code"),
                    p(
                        "Edit this file to customize your home page",
                        class_name="command-desc",
                    ),
                    class_name="command-text",
                ),
                class_name="command",
            ),
            div(
                span("2", class_name="command-icon"),
                div(
                    code("src/components/", class_name="command-code"),
                    p("Create reusable components", class_name="command-desc"),
                    class_name="command-text",
                ),
                class_name="command",
            ),
            div(
                span("3", class_name="command-icon"),
                div(
                    code("nitro build", class_name="command-code"),
                    p("Build for production when ready", class_name="command-desc"),
                    class_name="command-text",
                ),
                class_name="command",
            ),
        ),
        class_name="card",
    )

    # System info card
    system_info = div(
        h2("Environment", class_name="card-title"),
        div(
            div(
                p("Python", class_name="info-label"),
                p(python_version, class_name="info-value"),
                class_name="info-item",
            ),
            div(
                p("Nitro CLI", class_name="info-label"),
                p(f"v{nitro_version}", class_name="info-value"),
                class_name="info-item",
            ),
            class_name="info-grid",
        ),
        class_name="card",
    )

    # Links
    links = div(
        a(
            "Documentation",
            href="https://github.com/nitro-sh/nitro-cli",
            target="_blank",
        ),
        a("nitro-ui", href="https://github.com/nitro-sh/nitro-ui", target="_blank"),
        a(
            "Examples",
            href="https://github.com/nitro-sh/nitro-cli/tree/main/examples",
            target="_blank",
        ),
        class_name="links",
    )

    # Footer hint
    footer = p(
        "Edit ",
        code("src/pages/index.py"),
        " to replace this page",
        class_name="footer",
    )

    page = html(
        head(
            meta(charset="UTF-8"),
            meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            title("Welcome to Nitro"),
            meta(name="description", content="Your new Nitro project is ready"),
            link(rel="stylesheet", href="/styles/main.css"),
        ),
        body(
            main(
                section(
                    div("⚡", class_name="logo"),
                    h1("Nitro", class_name="brand"),
                    p("Your project is ready", class_name="tagline"),
                    status,
                    next_steps,
                    system_info,
                    links,
                    footer,
                    class_name="splash",
                ),
            ),
        ),
    )

    return Page(
        title="Welcome to Nitro",
        meta={"description": "Your new Nitro project is ready"},
        content=page,
    )
