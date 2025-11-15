"""Nitro configuration file."""

from nitro import Config

config = Config(
    site_name="My Portfolio",
    base_url="http://localhost:3000",
    # Build settings
    build_dir="build",
    source_dir="src",
    # Development server
    dev_server={"port": 3000, "host": "localhost", "live_reload": True},
    # Rendering options
    renderer={"pretty_print": True, "minify_html": False},
    # Metadata
    metadata={
        "author": "Your Name",
        "description": "My portfolio showcasing my work and projects",
        "keywords": ["portfolio", "projects", "work", "nitro"],
    },
)
