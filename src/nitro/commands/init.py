"""Init command for initializing Nitro in current directory."""

import click
from pathlib import Path

from ..utils import success, error, info, warning


DEFAULT_CONFIG = '''"""Nitro configuration file."""

# Site settings
title = "My Nitro Site"
base_url = "https://example.com"

# Directory settings
source_dir = "src"
build_dir = "build"

# Renderer settings
renderer = {
    "minify_html": False,
}

# Plugins (optional)
plugins = []
'''

DEFAULT_INDEX_PAGE = '''"""Home page."""

from nitro_ui import HTML, Head, Title, Meta, Body, Main, H1, Paragraph, Href
from nitro import Page


def render():
    content = HTML(
        Head(
            Title("Welcome to Nitro"),
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
        ),
        Body(
            Main(
                H1("Welcome to Nitro"),
                Paragraph(
                    "Your site is ready. Edit ",
                    Href("src/pages/index.py", href="#"),
                    " to get started."
                ),
            ),
        ),
    )

    return Page(
        title="Welcome to Nitro",
        content=content,
    )
'''

DEFAULT_GITIGNORE = """# Build output
build/
dist/

# Python
__pycache__/
*.py[cod]
*$py.class
.Python
*.so
.eggs/
*.egg-info/
*.egg

# Virtual environments
.venv/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Nitro
.nitro_cache/

# Environment
.env
.env.local
"""


@click.command()
@click.option("--force", "-f", is_flag=True, help="Overwrite existing files")
def init(force):
    """Initialize Nitro in the current directory."""
    cwd = Path.cwd()

    # Check if already a Nitro project
    config_file = cwd / "nitro.config.py"
    if config_file.exists() and not force:
        warning("This directory already contains a nitro.config.py")
        info("Use --force to overwrite existing files")
        return

    # Create directory structure
    directories = [
        "src/pages",
        "src/components",
        "src/styles",
        "src/data",
        "src/public",
    ]

    created_dirs = 0
    for dir_name in directories:
        dir_path = cwd / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs += 1

    if created_dirs > 0:
        success(f"Created {created_dirs} directories")

    # Create config file
    if not config_file.exists() or force:
        config_file.write_text(DEFAULT_CONFIG)
        success("Created nitro.config.py")

    # Create .gitignore
    gitignore_file = cwd / ".gitignore"
    if not gitignore_file.exists() or force:
        gitignore_file.write_text(DEFAULT_GITIGNORE)
        success("Created .gitignore")

    # Create starter index page
    index_file = cwd / "src" / "pages" / "index.py"
    if not index_file.exists() or force:
        index_file.write_text(DEFAULT_INDEX_PAGE)
        success("Created src/pages/index.py")

    info("\nNitro project initialized!")
    info("Run 'nitro dev' to start the development server")
