---
name: nitro-cli
description: Build static sites with Nitro CLI - a Python static site generator using nitro-ui for programmatic HTML generation instead of templates
---

# Nitro CLI - LLM Knowledge Base

This document contains everything needed to build static sites with Nitro CLI.

## Overview

Nitro CLI is a Python-based static site generator. Pages are written in Python using nitro-ui for HTML generation. The CLI provides scaffolding, a development server with live reload, and optimized production builds.

## Installation

```bash
pip install nitro-cli
```

## CLI Commands

### `nitro new <name>`
Create a new project.

```bash
nitro new my-site
nitro new my-site --no-git      # Skip git initialization
nitro new my-site --no-install  # Skip dependency installation
```

### `nitro dev` / `nitro serve`
Start development server with live reload.

```bash
nitro dev                    # Default: localhost:3000
nitro dev --port 8080        # Custom port
nitro dev --host 0.0.0.0     # Expose to network
nitro dev --open             # Open browser automatically
nitro dev --no-reload        # Disable live reload
```

### `nitro build`
Build for production with optimizations.

```bash
nitro build                  # Full build with all optimizations
nitro build --no-minify      # Skip HTML/CSS minification
nitro build --no-optimize    # Skip image optimization
nitro build --no-fingerprint # Skip cache-busting hashes
nitro build --no-responsive  # Skip responsive image generation
nitro build --no-islands     # Skip island processing
nitro build --clean          # Clean build dir first
nitro build --force          # Force full rebuild (ignore cache)
nitro build --output dist    # Custom output directory
nitro build --quiet          # Minimal output
nitro build --verbose        # Detailed output
nitro build --debug          # Full tracebacks
```

### `nitro preview`
Preview production build locally.

```bash
nitro preview                # Default: localhost:4000
nitro preview --port 5000    # Custom port
nitro preview --host 0.0.0.0 # Expose to network
nitro preview --open         # Open browser
```

### `nitro clean`
Remove build artifacts.

```bash
nitro clean           # Clean build + cache
nitro clean --all     # Clean everything
nitro clean --build   # Clean only build directory
nitro clean --cache   # Clean only cache
nitro clean --dry-run # Show what would be deleted
```

### `nitro deploy`
Deploy to hosting platforms.

```bash
nitro deploy                      # Auto-detect platform
nitro deploy --platform netlify   # Specific platform
nitro deploy --platform vercel
nitro deploy --platform cloudflare
nitro deploy --prod               # Production deployment
nitro deploy --no-build           # Skip build step
```

### `nitro info`
Show project and environment information.

```bash
nitro info
nitro info --json  # Output as JSON
```

## Project Structure

```
my-site/
├── nitro.config.py      # Project configuration
├── src/
│   ├── pages/           # Page files (→ HTML)
│   │   ├── index.py     # → /index.html
│   │   ├── about.py     # → /about.html
│   │   └── blog/
│   │       └── [slug].py  # Dynamic route
│   ├── components/      # Reusable components
│   ├── styles/          # CSS files
│   │   └── main.css     # → /assets/styles/main.css
│   └── data/            # JSON/YAML data files
├── static/              # Static assets (copied as-is)
└── build/               # Generated output (gitignored)
```

## Configuration

Create `nitro.config.py` in project root:

```python
from nitro import Config

config = Config(
    site_name="My Site",
    base_url="https://mysite.com",
    build_dir="build",       # Output directory
    source_dir="src",        # Source directory
    renderer={
        "pretty_print": False,  # Format HTML output
        "minify_html": False,   # Minify in dev (always minified in build)
    },
    plugins=[],              # Plugin list
)
```

## Writing Pages

### Basic Page Structure

Pages are Python files in `src/pages/` with a `render()` function:

```python
# src/pages/index.py
from nitro_ui.html import html, head, body, title, meta, h1, p
from nitro import Page

def render():
    page = html(
        head(
            meta(charset="UTF-8"),
            meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            title("My Page"),
        ),
        body(
            h1("Hello, World!"),
            p("Welcome to my site."),
        ),
    )

    return Page(
        title="My Page",
        meta={"description": "Page description"},
        content=page,
    )
```

### The Page Object

```python
from nitro import Page

Page(
    title="Page Title",           # Required: page title
    content=html_element,         # Required: nitro-ui element
    meta={"key": "value"},        # Optional: meta tags
    template="layout",            # Optional: template name
)
```

### File Path to URL Mapping

| File Path                     | Output URL             |
|-------------------------------|------------------------|
| `src/pages/index.py`          | `/index.html`          |
| `src/pages/about.py`          | `/about.html`          |
| `src/pages/blog/post.py`      | `/blog/post.html`      |
| `src/pages/docs/api/index.py` | `/docs/api/index.html` |

## nitro-ui HTML Module

Import HTML elements from `nitro_ui.html`:

```python
from nitro_ui.html import (
    # Document
    html, head, body, title, meta, link, style, script,

    # Sections
    header, footer, main, section, article, aside, nav,

    # Content
    div, span, p, a, img, br, hr,

    # Headings
    h1, h2, h3, h4, h5, h6,

    # Lists
    ul, ol, li, dl, dt, dd,

    # Tables
    table, thead, tbody, tfoot, tr, th, td,

    # Forms
    form, input_, label, button, select, option, textarea,

    # Text formatting
    strong, em, code, pre, blockquote, small, mark,

    # Media
    video, audio, source, picture, figure, figcaption,

    # Other
    iframe, canvas, details, summary,
)
```

### Element Usage

```python
# Basic element
div("Hello")                           # <div>Hello</div>

# With attributes
div("Content", class_name="container") # <div class="container">Content</div>
a("Click", href="/page")               # <a href="/page">Click</a>

# Nested elements
div(
    h1("Title"),
    p("Paragraph 1"),
    p("Paragraph 2"),
    class_name="content"
)

# Mixed content
p("Visit ", a("our site", href="/"), " for more.")

# Self-closing
img(src="/logo.png", alt="Logo")
meta(charset="UTF-8")
```

### Common Patterns

```python
# Navigation
nav(
    a("Home", href="/"),
    a("About", href="/about.html"),
    a("Contact", href="/contact.html"),
    class_name="nav"
)

# Card component
div(
    img(src="/image.jpg", alt="Card image"),
    h3("Card Title"),
    p("Card description"),
    a("Read more", href="/details"),
    class_name="card"
)

# Form
form(
    label("Email:", for_="email"),
    input_(type="email", id="email", name="email", required=True),
    label("Message:", for_="msg"),
    textarea(id="msg", name="message", rows="4"),
    button("Submit", type="submit"),
    action="/submit",
    method="post"
)
```

## Components

Create reusable components in `src/components/`:

```python
# src/components/card.py
from nitro_ui.html import div, h3, p, a, img

def Card(title, description, image=None, link=None):
    """Reusable card component."""
    children = []

    if image:
        children.append(img(src=image, alt=title))

    children.append(h3(title))
    children.append(p(description))

    if link:
        children.append(a("Learn more", href=link))

    return div(*children, class_name="card")
```

Use in pages:

```python
# src/pages/index.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.card import Card

def render():
    return html(
        body(
            Card("Title 1", "Description 1", link="/page1"),
            Card("Title 2", "Description 2", image="/img.jpg"),
        )
    )
```

## Dynamic Routes

Generate multiple pages from data using `[param].py` naming:

```python
# src/pages/blog/[slug].py
from nitro_ui.html import html, head, body, title, h1, p, article
from nitro import Page
from nitro_datastore import NitroDataStore

def get_paths():
    """Return list of parameter dicts for each page to generate."""
    data = NitroDataStore.from_file("src/data/posts.json")
    return [{"slug": post.slug, "title": post.title, "content": post.content}
            for post in data.posts]

def render(slug, title, content):
    """Render page for each set of parameters."""
    page = html(
        head(title(f"{title} - Blog")),
        body(
            article(
                h1(title),
                p(content),
            )
        )
    )

    return Page(title=title, content=page)
```

Output: `[slug].py` with `slug="hello-world"` → `build/blog/hello-world.html`

### Multiple Parameters

```python
# src/pages/[category]/[slug].py

def get_paths():
    return [
        {"category": "tech", "slug": "python"},
        {"category": "tech", "slug": "rust"},
        {"category": "life", "slug": "travel"},
    ]

def render(category, slug):
    # Generates:
    # - build/tech/python.html
    # - build/tech/rust.html
    # - build/life/travel.html
    ...
```

## Data Loading

Use nitro-datastore for loading JSON/YAML with dot notation:

```python
from nitro_datastore import NitroDataStore

# Load JSON file
data = NitroDataStore.from_file("src/data/site.json")

# Access with dot notation
site_name = data.site.name
posts = data.posts  # List access

# Iterate
for post in data.posts:
    print(post.title, post.slug)
```

Example data file:

```json
// src/data/site.json
{
  "site": {
    "name": "My Site",
    "tagline": "Built with Nitro"
  },
  "posts": [
    {"slug": "hello", "title": "Hello World"},
    {"slug": "intro", "title": "Introduction"}
  ]
}
```

## Styling

### CSS Files

Place CSS in `src/styles/`. They're copied to `build/assets/styles/`:

```css
/* src/styles/main.css */
:root {
    --primary: #6366f1;
    --text: #1e293b;
}

body {
    font-family: system-ui, sans-serif;
    color: var(--text);
}
```

Link in pages:

```python
from nitro_ui.html import link

head(
    link(rel="stylesheet", href="/assets/styles/main.css"),
)
```

### Inline Styles

```python
from nitro_ui.html import style, div

# In head
style("""
    .container { max-width: 1200px; margin: 0 auto; }
    .hero { padding: 4rem 2rem; }
""")

# Inline on element
div("Content", style="padding: 1rem; background: #f0f0f0;")
```

## Static Assets

Place files in `static/` directory - they're copied to build root:

```
static/
├── favicon.ico      → build/favicon.ico
├── robots.txt       → build/robots.txt
└── images/
    └── logo.png     → build/images/logo.png
```

Reference in HTML:

```python
img(src="/images/logo.png", alt="Logo")
link(rel="icon", href="/favicon.ico")
```

## Build Optimizations

Production builds (`nitro build`) include:

1. **HTML Minification** - Removes whitespace, comments
2. **CSS Minification** - Compresses CSS files
3. **Image Optimization** - Compresses JPG/PNG with Pillow
4. **Asset Fingerprinting** - Adds content hashes for cache busting
5. **Sitemap Generation** - Creates sitemap.xml
6. **Robots.txt** - Creates robots.txt

## Live Reload

The dev server injects a WebSocket client that reloads the page when files change:

- `src/pages/*.py` - Rebuilds changed page
- `src/components/*.py` - Rebuilds all pages
- `src/styles/*.css` - Copies assets, reloads
- `nitro.config.py` - Full rebuild

## Deployment

### Netlify

```bash
nitro deploy --platform netlify --prod
```

Or create `netlify.toml`:

```toml
[build]
  command = "pip install nitro-cli && nitro build"
  publish = "build"
```

### Vercel

```bash
nitro deploy --platform vercel --prod
```

### Cloudflare Pages

```bash
nitro deploy --platform cloudflare --prod
```

## Common Patterns

### Layout Component

```python
# src/components/layout.py
from nitro_ui.html import html, head, body, title, meta, link, main, header, footer

def Layout(page_title, children, description=None):
    return html(
        head(
            meta(charset="UTF-8"),
            meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            title(page_title),
            meta(name="description", content=description or page_title),
            link(rel="stylesheet", href="/assets/styles/main.css"),
        ),
        body(
            header(),  # nav content
            main(*children if isinstance(children, (list, tuple)) else [children]),
            footer(),  # footer content
        ),
    )
```

### SEO Meta Tags

```python
head(
    title("Page Title"),
    meta(name="description", content="Page description for search engines"),
    meta(name="keywords", content="keyword1, keyword2"),
    meta(property="og:title", content="Title for social sharing"),
    meta(property="og:description", content="Description for social"),
    meta(property="og:image", content="https://site.com/image.jpg"),
    meta(name="twitter:card", content="summary_large_image"),
    link(rel="canonical", href="https://site.com/page"),
)
```

### Responsive Images

```python
picture(
    source(srcset="/img/hero.avif", type="image/avif"),
    source(srcset="/img/hero.webp", type="image/webp"),
    img(src="/img/hero.jpg", alt="Hero image", loading="lazy"),
)
```

### Conditional Content

```python
def render():
    is_production = os.getenv("NODE_ENV") == "production"

    analytics = script(src="/analytics.js") if is_production else None

    return html(
        head(title("Page"), analytics),
        body(h1("Page content")),
    )
```

## Troubleshooting

### Common Errors

**"Page missing render() function"**
- Every page file needs a `def render():` function

**"Dynamic page missing get_paths() function"**
- Files named `[param].py` need both `get_paths()` and `render()`

**Import errors for components**
- Add `sys.path.insert(0, str(Path(__file__).parent.parent))` before importing

**CSS not loading**
- Use absolute paths: `/assets/styles/main.css`
- Check file is in `src/styles/`

### Debug Mode

```bash
nitro build --debug   # Full tracebacks
nitro dev --verbose   # Detailed logging
```

## Dependencies

- **nitro-ui** >= 1.0.4 - HTML element builder
- **nitro-datastore** >= 1.0.2 - Data loading with dot notation
- **nitro-dispatch** >= 1.0.0 - Plugin system hooks

## Version

Current: nitro-cli 1.0.5
