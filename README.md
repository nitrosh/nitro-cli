# Nitro CLI

> A powerful static site generator built with Python

Nitro CLI is a command-line tool that helps you build beautiful static websites using Python and [nitro-ui](https://github.com/nitrosh/nitro-ui). Write your pages in Python, leverage the power of nitro-ui's HTML builder, and deploy static sites with ease.

## Features

- **Python-Powered**: Write pages using Python and nitro-ui instead of template languages
- **Component-Based**: Reusable components with a clean architecture
- **Fast Development**: Built-in development server with hot reload
- **Incremental Builds**: Only rebuild changed pages for faster iterations
- **Parallel Generation**: Multi-threaded page generation for large sites
- **Production Ready**: Optimized builds with minification and asset optimization
- **Markdown Support**: Write content in Markdown with frontmatter
- **Dynamic Routes**: Generate pages from data with `[slug].py` pattern
- **Content Collections**: Typed content with schema validation (like Astro)
- **Image Optimization**: Responsive images with WebP/AVIF conversion
- **Islands Architecture**: Partial hydration for interactive components
- **RSS/Atom Feeds**: Built-in feed generation
- **One-Click Deploy**: Deploy to Netlify, Vercel, or Cloudflare Pages
- **Flexible Data**: Load JSON/YAML data with [nitro-datastore](https://github.com/nitrosh/nitro-datastore)
- **Extensible**: Plugin system powered by [nitro-dispatch](https://github.com/nitrosh/nitro-dispatch)

## Installation

### From PyPI (coming soon)

```bash
pip install nitro-cli
```

### From Source (Development)

```bash
git clone https://github.com/nitrosh/nitro-cli.git
cd nitro-cli
pip install -e .
```

## Quick Start

### 1. Create a New Project

```bash
nitro new my-site
cd my-site
```

### 2. Start Development Server

```bash
nitro dev
```

Or with more options:

```bash
nitro serve --open  # Auto-open browser
```

Visit http://localhost:3000 to see your site. The server automatically:
- Generates your site if the build directory is empty
- Watches for file changes
- Reloads the browser when changes are detected

### 3. Build for Production

```bash
nitro build
```

Your optimized site will be in the `build/` directory.

### 4. Deploy

```bash
nitro deploy --prod
```

## Project Structure

When you create a new project, Nitro generates the following structure:

```
my-site/
├── nitro.config.py          # Configuration file
├── requirements.txt
├── .gitignore
├── src/
│   ├── components/          # Reusable nitro-ui components
│   │   ├── header.py
│   │   └── footer.py
│   ├── pages/              # Page definitions (route = file path)
│   │   ├── index.py        # -> /index.html
│   │   ├── about.py        # -> /about.html
│   │   └── blog/
│   │       └── [slug].py   # -> /blog/{slug}.html (dynamic route)
│   ├── content/            # Markdown content collections
│   │   ├── blog/           # Blog posts
│   │   └── docs/           # Documentation
│   ├── data/               # JSON/YAML data files
│   ├── styles/             # CSS stylesheets
│   ├── public/             # Static assets (copied to build root)
│   └── plugins/            # Project-specific plugins
├── build/                  # Generated output
└── .nitro/                 # Nitro cache & metadata
    └── cache.json          # Build cache for incremental builds
```

## Commands

### `nitro` (no arguments)

Display welcome banner with available commands and project info.

```bash
nitro
```

### `nitro new`

Create a new Nitro project.

```bash
nitro new PROJECT_NAME [OPTIONS]

Options:
  --no-git                                 Skip git initialization
  --no-install                             Skip dependency installation
  -v, --verbose                            Enable verbose output
  --debug                                  Enable debug mode with full tracebacks
  --log-file PATH                          Write logs to a file
```

### `nitro dev`

Start development server with sensible defaults (alias for `serve`).

```bash
nitro dev [OPTIONS]

Options:
  -p, --port INTEGER        Port number (default: 3000)
  -h, --host TEXT          Host address (default: localhost)
  --open                   Auto-open browser
  -v, --verbose            Enable verbose output
```

### `nitro serve`

Start a local development server with live reload.

```bash
nitro serve [OPTIONS]

Options:
  -p, --port INTEGER        Port number (default: 3000)
  -h, --host TEXT          Host address (default: localhost)
  --open                   Auto-open browser
  --no-reload              Disable live reload
  -v, --verbose            Enable verbose output
  --debug                  Enable debug mode with full tracebacks
  --log-file PATH          Write logs to a file
```

### `nitro build`

Build the site for production with optimization.

```bash
nitro build [OPTIONS]

Options:
  --minify/--no-minify           Minify HTML and CSS (default: enabled)
  --optimize/--no-optimize       Optimize images and assets (default: enabled)
  --responsive/--no-responsive   Generate responsive images with WebP/AVIF (default: disabled)
  --fingerprint/--no-fingerprint Add content hashes to asset filenames (default: enabled)
  --islands/--no-islands         Process islands and inject hydration scripts (default: enabled)
  -o, --output PATH              Output directory (default: build/)
  --clean                        Clean build directory before building
  -f, --force                    Force full rebuild, ignore cache
  -v, --verbose                  Enable verbose output
  -q, --quiet                    Only show errors and final summary
  --debug                        Enable debug mode with full tracebacks
  --log-file PATH                Write logs to a file
```

Creates an optimized production build with:
- HTML and CSS minification
- Image optimization
- Responsive images (WebP/AVIF) with `--responsive`
- Asset fingerprinting for cache busting
- Islands hydration scripts
- Sitemap generation (sitemap.xml)
- SEO-friendly robots.txt
- Asset manifest with file hashes
- Build statistics and summary

### `nitro preview`

Preview production build locally.

```bash
nitro preview [OPTIONS]

Options:
  -p, --port INTEGER        Port number (default: 4000)
  -h, --host TEXT          Host address (default: localhost)
  --open                   Auto-open browser
  -v, --verbose            Enable verbose output
```

### `nitro clean`

Clean build artifacts and cache.

```bash
nitro clean [OPTIONS]

Options:
  --build                  Clean build directory only
  --cache                  Clean cache directory only
  --all                    Clean everything (default)
  --dry-run               Show what would be deleted without deleting
  -v, --verbose            Enable verbose output
```

### `nitro info`

Display project and environment information.

```bash
nitro info [OPTIONS]

Options:
  -v, --verbose            Show detailed information
```

Shows:
- Nitro version
- Python version
- Project configuration
- Dependencies status
- File counts and sizes

### `nitro deploy`

Deploy the site to a hosting platform.

```bash
nitro deploy [OPTIONS]

Options:
  -p, --platform [auto|netlify|vercel|cloudflare]  Deployment platform (auto-detect if not specified)
  --build/--no-build       Build before deploying (default: enabled)
  --prod                   Deploy to production (not preview)
  -v, --verbose            Enable verbose output
```

Supports:
- **Netlify** - Requires `netlify-cli` (`npm install -g netlify-cli`)
- **Vercel** - Requires `vercel` (`npm install -g vercel`)
- **Cloudflare Pages** - Requires `wrangler` (`npm install -g wrangler`)

Auto-detects platform based on:
1. Config files (`netlify.toml`, `vercel.json`, `wrangler.toml`)
2. Installed CLI tools

## Writing Pages

Pages are Python files that return nitro-ui components:

```python
# src/pages/index.py
from nitro_ui import HTML, Head, Body, Div, H1, Paragraph, Title, Meta, Link
from nitro import Page, load_data
import sys
from pathlib import Path

# Add parent directory to path for component imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.header import Header
from components.footer import Footer

def render():
    # Load data from JSON file
    data = load_data("src/data/site.json")

    return Page(
        title=f"Home - {data.site.name}",
        meta={
            "description": data.site.description,
            "keywords": "static, site, generator"
        },
        content=HTML(
            Head(
                Meta(charset="UTF-8"),
                Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
                Title(f"Home - {data.site.name}"),
                Link(rel="stylesheet", href="/assets/styles/main.css"),
            ),
            Body(
                Header(data.site.name),
                Div(
                    H1("Welcome!"),
                    Paragraph("This is built with Nitro + nitro-ui!")
                ),
                Footer()
            )
        )
    )
```

## Dynamic Routes

Create pages from data using the `[slug].py` pattern:

```python
# src/pages/blog/[slug].py
from nitro_ui import HTML, Head, Body, Article, H1, Div, Title
from nitro import Page, load_data

def get_paths():
    """Return list of paths to generate."""
    # Load data - returns a NitroDataStore for dictionary access
    data = load_data("src/data/posts.json")
    # Access the posts array using dot notation
    return [
        {"slug": post["slug"], "title": post["title"], "content": post["content"]}
        for post in data.posts
    ]

def render(slug, title, content):
    """Render a single blog post page."""
    return Page(
        title=title,
        content=HTML(
            Head(Title(title)),
            Body(
                Article(
                    H1(title),
                    Div(content)
                )
            )
        )
    )
```

**src/data/posts.json:**
```json
{
  "posts": [
    {"slug": "hello-world", "title": "Hello World", "content": "My first post!"},
    {"slug": "getting-started", "title": "Getting Started", "content": "How to begin..."}
  ]
}
```

This generates `/blog/hello-world.html`, `/blog/getting-started.html`, etc.

## Markdown Support

Write content in Markdown with YAML frontmatter:

```markdown
---
title: My First Post
date: 2024-01-15
author: Jane Doe
tags:
  - python
  - web
draft: false
---

# Hello World

This is my first blog post written in **Markdown**.

- Feature 1
- Feature 2
- Feature 3
```

Use in pages:

```python
from nitro import parse_markdown_file, find_markdown_files

# Parse a single file
doc = parse_markdown_file("content/blog/hello-world.md")
print(doc.title)        # "My First Post"
print(doc.date)         # datetime object
print(doc.content)      # HTML string
print(doc.frontmatter)  # Full frontmatter dict

# Find all markdown files
posts = find_markdown_files("content/blog")
for post in posts:
    print(post.slug)    # "hello-world"
```

## Content Collections

Define typed content collections with schema validation:

```python
# content.config.py
from nitro import CollectionSchema, StringField, DateField, ListField, BooleanField

collections = {
    "blog": CollectionSchema(
        fields={
            "title": StringField(required=True),
            "date": DateField(required=True),
            "author": StringField(required=False, default="Anonymous"),
            "tags": ListField(item_type=StringField()),
            "draft": BooleanField(default=False),
        }
    ),
    "docs": CollectionSchema(
        fields={
            "title": StringField(required=True),
            "order": NumberField(integer_only=True, default=0),
            "category": EnumField(choices=["guide", "api", "tutorial"]),
        }
    ),
}
```

Use collections in pages:

```python
from nitro import CollectionRegistry

# Load collections
registry = CollectionRegistry(project_root)
registry.load_from_config("content.config.py")

# Get a collection
blog = registry.get("blog")

# Query entries
recent_posts = blog.sort("date", reverse=True)[:5]
tutorials = blog.where(tags=lambda t: "tutorial" in t)
by_author = blog.group_by("author")

# Get single entry
post = blog.get("hello-world")
print(post.data["title"])
print(post.content)  # HTML
```

Available field types:
- `StringField` - Text with optional min/max length, pattern, choices
- `NumberField` - Integer or float with min/max values
- `BooleanField` - True/false
- `DateField` - Date/datetime parsing
- `ListField` - Arrays with optional item type validation
- `EnumField` - Predefined choices
- `SlugField` - URL-safe slugs

Convenience schemas:
```python
from nitro import blog_schema, docs_schema

# Pre-configured blog schema
schema = blog_schema(
    featured=BooleanField(default=False)  # Add custom fields
)
```

## Image Optimization

Nitro can automatically optimize images during build:

### Basic Optimization

```bash
nitro build --optimize  # Enabled by default
```

Compresses JPEG, PNG images using Pillow.

### Responsive Images

```bash
nitro build --responsive
```

Generates:
- Multiple sizes (320, 640, 768, 1024, 1280, 1920px)
- WebP and AVIF formats
- Automatic `<picture>` elements with `srcset`
- Lazy loading attributes

Before:
```html
<img src="/images/hero.jpg" alt="Hero">
```

After:
```html
<picture>
  <source type="image/avif" srcset="/_images/hero-320w-a1b2c3d4.avif 320w, ..." sizes="...">
  <source type="image/webp" srcset="/_images/hero-320w-a1b2c3d4.webp 320w, ..." sizes="...">
  <img src="/_images/hero-1920w-a1b2c3d4.jpg" srcset="..." alt="Hero" loading="lazy" width="1920" height="1080">
</picture>
```

### In Templates

```python
from nitro import responsive_image, lazy_image

# Simple lazy loading
lazy_image("/images/photo.jpg", alt="Photo", css_class="rounded")

# Responsive with custom sizes
responsive_image(
    "/images/hero.jpg",
    alt="Hero image",
    sizes="(max-width: 640px) 100vw, 50vw",
    widths=[320, 640, 1024, 1920]
)
```

## Islands Architecture

Islands allow interactive components to be hydrated on the client while the rest of the page remains static HTML.

### Creating Islands

```python
from nitro import Island, island, client_component
from nitro_ui import Div, Button

# Method 1: Island class
counter_island = Island(
    name="counter",
    component=Counter,
    props={"initial": 0},
    client="visible"  # Hydration strategy
)

# Method 2: island() function
search = island(SearchBox, client="interaction", placeholder="Search...")

# Method 3: Decorator
@client_component(strategy="idle")
def Counter(initial=0):
    return Div(
        Button("-"),
        Span(str(initial)),
        Button("+")
    )
```

### Hydration Strategies

- `load` - Hydrate immediately when page loads
- `idle` - Hydrate when browser is idle (default)
- `visible` - Hydrate when component enters viewport
- `media` - Hydrate when media query matches
- `interaction` - Hydrate on first user interaction (click, focus, etc.)
- `none` - Never hydrate (static only)

### Convenience Functions

```python
from nitro import lazy_island, eager_island, interactive_island, static_island

# Hydrates when visible (lazy loading)
lazy_island(ImageGallery, images=gallery_images)

# Hydrates immediately
eager_island(CriticalWidget, data=widget_data)

# Hydrates on interaction
interactive_island(Dropdown, options=menu_items)

# Never hydrates
static_island(StaticContent, content=html_content)
```

### In Pages

```python
def render():
    return Page(
        content=HTML(
            Body(
                Header(),  # Static
                Counter(initial=5).render(),  # Island - hydrates on idle
                lazy_island(Comments, post_id=123).render(),  # Hydrates when visible
                Footer()  # Static
            )
        )
    )
```

### Client-Side Registration

Register your island components on the client:

```javascript
// Register component for hydration
window.__registerIsland('counter', function(props) {
    // Return your interactive component
    return new CounterComponent(props);
});
```

## RSS/Atom Feeds

Generate feeds for your content:

```python
from nitro.core import Bundler
from datetime import datetime

bundler = Bundler(build_dir)

# RSS 2.0 feed
bundler.generate_rss_feed(
    items=[
        {
            "title": "My Post",
            "link": "https://mysite.com/blog/my-post",
            "description": "Post summary",
            "pubDate": datetime(2024, 1, 15),
            "guid": "https://mysite.com/blog/my-post"
        }
    ],
    base_url="https://mysite.com",
    output_path=build_dir / "feed.xml",
    title="My Blog",
    description="Latest posts from my blog"
)

# Atom feed
bundler.generate_atom_feed(
    items=[...],
    base_url="https://mysite.com",
    output_path=build_dir / "atom.xml",
    title="My Blog",
    author_name="Jane Doe"
)
```

## Creating Components

Components are reusable nitro-ui elements:

```python
# src/components/header.py
from nitro_ui import Header as UIHeader, Nav, A, Div, H1

def Header(site_name="My Site"):
    logo = H1(site_name, class_name="logo")

    nav = Nav(
        A("Home", href="/"),
        A("About", href="/about.html"),
        class_name="nav"
    )

    header_content = Div(logo, nav, class_name="header-content")
    header = UIHeader(header_content, class_name="header")

    return header
```

## Working with Data

Nitro integrates with [nitro-datastore](https://github.com/nitrosh/nitro-datastore) for flexible data management.

### Quick Example

```python
from nitro import load_data

# Load data from JSON file
data = load_data('src/data/site.json')

# Access with dot notation
print(data.site.name)
print(data.site.tagline)

# Dictionary access
print(data['site']['name'])

# Path-based access with defaults
print(data.get('site.name', 'Default Name'))
```

**src/data/site.json:**
```json
{
  "site": {
    "name": "My Portfolio",
    "description": "Building amazing things",
    "author": "Alice Developer"
  },
  "features": [
    {"name": "Fast", "description": "Lightning fast builds"},
    {"name": "Simple", "description": "Easy to use"}
  ]
}
```

### Loading from Directory

```python
# Automatically merges all JSON files in the directory
config = load_data('src/data/config/')
```

## Incremental Builds

Nitro tracks file hashes to only rebuild changed pages:

```bash
# Normal build (uses cache)
nitro build

# Force full rebuild
nitro build --force

# Clean and rebuild
nitro build --clean
```

Cache is stored in `.nitro/cache.json` and tracks:
- Page file hashes
- Component dependencies
- Data file changes

## Configuration

Configure your project in `nitro.config.py`:

```python
from nitro import Config

config = Config(
    site_name="My Website",
    base_url="https://mysite.com",

    # Build settings
    build_dir="build",
    source_dir="src",

    # Development server
    dev_server={
        "port": 3000,
        "host": "localhost",
        "live_reload": True
    },

    # Rendering options
    renderer={
        "pretty_print": False,
        "minify_html": True
    },

    # Metadata
    metadata={
        "author": "Your Name",
        "description": "Site description"
    },

    # Plugins
    plugins=[]
)
```

## Plugin System

Nitro uses [nitro-dispatch](https://github.com/nitrosh/nitro-dispatch) for its plugin system. Create a plugin by extending `NitroPlugin`:

```python
# src/plugins/analytics.py
from nitro.plugins import NitroPlugin, hook

class Plugin(NitroPlugin):
    """Plugin class must be named 'Plugin' for auto-discovery."""

    name = "analytics"
    version = "1.0.0"
    description = "Adds analytics tracking to pages"
    author = "Your Name"

    @hook("nitro.pre_build")
    def on_pre_build(self, data):
        """Called before build starts."""
        print(f"Building to {data.get('build_dir')}")
        return data

    @hook("nitro.post_generate", priority=50)
    def inject_tracking(self, data):
        """Inject analytics script into generated HTML."""
        html = data.get('output', '')
        script = '<script src="/assets/js/analytics.js"></script>'
        data['output'] = html.replace('</body>', f'{script}</body>')
        return data
```

### Available Hooks

- `nitro.init` - Plugin initialization
- `nitro.pre_generate` - Before page generation
- `nitro.post_generate` - After page generation (can modify output)
- `nitro.pre_build` - Before production build
- `nitro.post_build` - After production build
- `nitro.process_data` - Process data files
- `nitro.add_commands` - Add custom CLI commands

### Hook Options

```python
@hook("nitro.post_generate", priority=100, timeout=5.0)
def high_priority_hook(self, data):
    """Higher priority hooks execute first. Timeout prevents hanging."""
    return data
```

### Register Plugins

Register plugins in `nitro.config.py`:

```python
config = Config(
    plugins=[
        "analytics",  # Loads src/plugins/analytics.py
    ]
)
```

## Asset Fingerprinting

Nitro adds content hashes to CSS and JS filenames for cache busting:

```bash
nitro build --fingerprint  # Enabled by default
```

Before:
```html
<link href="/assets/styles/main.css" rel="stylesheet">
```

After:
```html
<link href="/assets/styles/main.a1b2c3d4.css" rel="stylesheet">
```

## Requirements

- Python 3.8+
- nitro-ui
- nitro-datastore
- nitro-dispatch

Optional dependencies:
- `Pillow` - Image optimization
- `pillow-avif-plugin` - AVIF support
- `csscompressor` - CSS minification
- `python-frontmatter` - Markdown frontmatter
- `markdown` - Markdown processing

## Development

### Setting Up Development Environment

```bash
git clone https://github.com/nitrosh/nitro-cli.git
cd nitro-cli
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Quality

```bash
flake8 src/
black src/
```

## Ecosystem

Nitro CLI is part of the Nitro ecosystem:

- [nitro-ui](https://github.com/nitrosh/nitro-ui) - Python HTML generation library
- [nitro-datastore](https://github.com/nitrosh/nitro-datastore) - Flexible data loading with dot notation
- [nitro-dispatch](https://github.com/nitrosh/nitro-dispatch) - Plugin system and event hooks

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

If you encounter any issues or have questions:
- [GitHub Issues](https://github.com/nitrosh/nitro-cli/issues)
