# Nitro CLI

A static site generator that lets you build websites using Python and [nitro-ui](https://github.com/nitrosh/nitro-ui).

## Features

- **Python-Powered** - Write pages in Python with nitro-ui instead of template languages
- **Live Reload** - Development server with automatic browser refresh
- **Incremental Builds** - Only rebuild changed pages
- **Dynamic Routes** - Generate pages from data with `[slug].py` pattern
- **Markdown Support** - Content with YAML frontmatter
- **Content Collections** - Typed content with schema validation
- **Image Optimization** - Responsive images with WebP/AVIF conversion
- **Islands Architecture** - Partial hydration for interactive components
- **One-Click Deploy** - Netlify, Vercel, or Cloudflare Pages

## Installation

```bash
pip install nitro-cli
```

## Quick Start

```bash
nitro new my-site
cd my-site
nitro dev
```

Visit http://localhost:3000. Build for production with `nitro build`.

## Writing Pages

Pages are Python files in `src/pages/` that export a `render()` function:

```python
# src/pages/index.py
from nitro_ui import HTML, Head, Body, H1, Title
from nitro import Page

def render():
    return Page(
        title="Home",
        content=HTML(
            Head(Title("Home")),
            Body(H1("Welcome!"))
        )
    )
```

Output paths mirror the file structure: `src/pages/about.py` → `build/about.html`

## Dynamic Routes

Generate multiple pages from data using `[param].py` naming:

```python
# src/pages/blog/[slug].py
from nitro import Page, load_data

def get_paths():
    data = load_data("src/data/posts.json")
    return [{"slug": p["slug"], "title": p["title"]} for p in data.posts]

def render(slug, title):
    return Page(title=title, content=...)
```

## Commands

| Command | Description |
|---------|-------------|
| `nitro new <name>` | Create new project |
| `nitro dev` | Start dev server with live reload |
| `nitro build` | Build for production |
| `nitro preview` | Preview production build |
| `nitro clean` | Remove build artifacts |
| `nitro deploy` | Deploy to hosting platform |

Run `nitro <command> --help` for options.

## Configuration

```python
# nitro.config.py
from nitro import Config

config = Config(
    site_name="My Site",
    base_url="https://mysite.com",
    dev_server={"port": 3000},
    renderer={"minify_html": True}
)
```

## Ecosystem

- [nitro-ui](https://github.com/nitrosh/nitro-ui) - HTML generation library
- [nitro-datastore](https://github.com/nitrosh/nitro-datastore) - Data loading with dot notation
- [nitro-dispatch](https://github.com/nitrosh/nitro-dispatch) - Plugin system

## License

MIT