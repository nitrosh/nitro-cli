"""Nitro configuration file."""

from nitro import Config

config = Config(
    site_name="My Nitro Site",
    base_url="http://localhost:3000",
    build_dir="build",
    source_dir="src",
    renderer={
        "pretty_print": True,
        "minify_html": False,
    },
)
