"""Welcome page - the default splash screen for new Nitro projects."""

import sys

from nitro_ui.html import (
    html,
    head,
    body,
    title,
    meta,
    style,
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
python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

try:
    from nitro import __version__ as nitro_version
except ImportError:
    nitro_version = "1.0.0"


def render():
    """Render the welcome splash page."""

    # Inline styles for splash page (self-contained)
    styles = """
        :root {
            --primary: #8b5cf6;
            --primary-dark: #7c3aed;
            --bg: #0f0f10;
            --bg-card: #18181b;
            --text: #fafafa;
            --text-muted: #a1a1aa;
            --border: #27272a;
            --success: #22c55e;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            line-height: 1.6;
        }

        .splash {
            max-width: 640px;
            width: 100%;
            text-align: center;
        }

        .logo {
            font-size: 4rem;
            margin-bottom: 0.5rem;
            filter: drop-shadow(0 0 20px rgba(139, 92, 246, 0.5));
        }

        .brand {
            font-size: 2.5rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            background: linear-gradient(135deg, var(--primary) 0%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
        }

        .tagline {
            font-size: 1.25rem;
            color: var(--text-muted);
            margin-bottom: 2.5rem;
        }

        .status {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 9999px;
            padding: 0.5rem 1rem;
            font-size: 0.875rem;
            margin-bottom: 3rem;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background: var(--success);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
            text-align: left;
        }

        .card-title {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--text-muted);
            margin-bottom: 1rem;
        }

        .command {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.75rem 0;
            border-bottom: 1px solid var(--border);
        }

        .command:last-child {
            border-bottom: none;
        }

        .command-icon {
            font-size: 1.25rem;
            width: 2rem;
            text-align: center;
        }

        .command-text {
            flex: 1;
        }

        .command-code {
            font-family: "SF Mono", "Fira Code", "Consolas", monospace;
            font-size: 0.9375rem;
            color: var(--primary);
        }

        .command-desc {
            font-size: 0.8125rem;
            color: var(--text-muted);
        }

        .info-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }

        .info-item {
            background: var(--bg);
            border-radius: 8px;
            padding: 1rem;
        }

        .info-label {
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-bottom: 0.25rem;
        }

        .info-value {
            font-family: "SF Mono", "Fira Code", "Consolas", monospace;
            font-size: 0.9375rem;
        }

        .links {
            display: flex;
            gap: 1.5rem;
            justify-content: center;
            flex-wrap: wrap;
        }

        .links a {
            color: var(--text-muted);
            text-decoration: none;
            font-size: 0.875rem;
            transition: color 0.2s;
        }

        .links a:hover {
            color: var(--primary);
        }

        .footer {
            margin-top: 3rem;
            color: var(--text-muted);
            font-size: 0.8125rem;
        }

        .footer code {
            background: var(--bg-card);
            padding: 0.2em 0.5em;
            border-radius: 4px;
            font-family: "SF Mono", "Fira Code", "Consolas", monospace;
        }

        @media (max-width: 480px) {
            .brand { font-size: 2rem; }
            .tagline { font-size: 1rem; }
            .info-grid { grid-template-columns: 1fr; }
        }
    """

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
                    p("Edit this file to customize your home page", class_name="command-desc"),
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
        a("Documentation", href="https://github.com/nitro-sh/nitro-cli", target="_blank"),
        a("nitro-ui", href="https://github.com/nitro-sh/nitro-ui", target="_blank"),
        a("Examples", href="https://github.com/nitro-sh/nitro-cli/tree/main/examples", target="_blank"),
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
            style(styles),
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
