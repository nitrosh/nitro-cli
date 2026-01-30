# Nitro CLI

A static site generator that lets you build websites using Python and [nitro-ui](https://github.com/nitrosh/nitro-ui).

## Features

- **Python-Powered** - Write pages in Python with nitro-ui instead of template languages
- **Live Reload** - Development server with automatic browser refresh
- **Incremental Builds** - Only rebuild changed pages
- **Dynamic Routes** - Generate pages from data with `[slug].py` pattern
- **Draft Pages** - Mark pages as drafts to exclude from production builds
- **Environment Variables** - Auto-load `.env` files with `from nitro import env`
- **Image Optimization** - Responsive images with WebP/AVIF conversion
- **Islands Architecture** - Partial hydration for interactive components
- **Plugin System** - Extend the build lifecycle with nitro-dispatch hooks
- **One-Click Deploy** - Netlify, Vercel, or Cloudflare Pages

## Installation

```bash
pip install nitro-cli
```

### AI Assistant Integration

Add Nitro CLI knowledge to your AI coding assistant:

```bash
npx skills add nitrosh/nitro-cli
```

This enables AI assistants like Claude Code to understand Nitro CLI and generate correct nitro-ui code.

## Quick Start

```bash
nitro new my-site
cd my-site
nitro dev
```

Visit <http://localhost:3000>. Build for production with `nitro build`.

## Writing Pages

Pages are Python files in `src/pages/` that export a `render()` function:

```python
# src/pages/index.py
from nitro_ui import HTML, Head, Body, Title, Meta, H1
from nitro import Page

def render():
    return Page(
        title="Home",
        content=HTML(
            Head(
                Meta(charset="UTF-8"),
                Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
                Title("Home"),
            ),
            Body(H1("Welcome!"))
        )
    )
```

Output paths mirror the file structure: `src/pages/about.py` → `build/about.html`

## Dynamic Routes

Generate multiple pages from data using `[param].py` naming:

```python
# src/pages/blog/[slug].py
from nitro import Page
from nitro_datastore import NitroDataStore

def get_paths():
    data = NitroDataStore.from_file("src/data/posts.json")
    return [{"slug": p.slug, "title": p.title} for p in data.posts]

def render(slug, title):
    return Page(title=title, content=...)
```

## Commands

| Command            | Description                        |
|--------------------|------------------------------------|
| `nitro new <name>` | Create new project                 |
| `nitro init`       | Initialize Nitro in current dir    |
| `nitro dev`        | Start dev server with live reload  |
| `nitro build`      | Build for production               |
| `nitro preview`    | Preview production build           |
| `nitro routes`     | List all routes                    |
| `nitro check`      | Validate site without building     |
| `nitro export`     | Export site as zip archive         |
| `nitro clean`      | Remove build artifacts             |
| `nitro deploy`     | Deploy to hosting platform         |
| `nitro info`       | Show project and environment info  |

Run `nitro <command> --help` for options.

## Configuration

```python
# nitro.config.py
from nitro import Config

config = Config(
    site_name="My Site",
    base_url="https://mysite.com",
    renderer={"minify_html": True},
    plugins=[],
)
```

## Ecosystem

- **[nitro-ui](https://github.com/nitrosh/nitro-ui)** - Programmatic HTML generation
- **[nitro-datastore](https://github.com/nitrosh/nitro-datastore)** - Data loading with dot notation access
- **[nitro-dispatch](https://github.com/nitrosh/nitro-dispatch)** - Plugin system
- **[nitro-validate](https://github.com/nitrosh/nitro-validate)** - Data validation

## License

This project is licensed under the BSD 3-Clause License. See the [LICENSE](LICENSE) file for details.
