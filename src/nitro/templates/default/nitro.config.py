"""Nitro configuration file."""

from nitro import Config

config = Config(
    site_name="My Nitro Site",
    base_url="http://localhost:3000",
    build_dir="build",
    source_dir="src",
    dev_server={
        "port": 3000,
        "host": "localhost",
        "live_reload": True,
    },
    renderer={
        "pretty_print": True,
        "minify_html": False,
    },
    metadata={
        "author": "Your Name",
        "description": "Site Description",
    },
)
