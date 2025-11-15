# Nitro CLI

> A powerful static site generator built on YDNATL

Nitro CLI is a command-line tool that helps you build beautiful static websites using Python and [YDNATL](https://github.com/sn/ydnatl). Write your pages in Python, leverage the power of YDNATL's HTML builder, and deploy static sites with ease.

## Features

- **Python-Powered**: Write pages using Python and YDNATL instead of template languages
- **Component-Based**: Reusable components with a clean architecture
- **Fast Development**: Built-in development server with hot reload
- **Production Ready**: Optimized builds with minification and asset optimization
- **Extensible**: Plugin system for adding custom functionality
- **Multiple Templates**: Start quickly with website, portfolio, or blog templates

## Installation

### From PyPI (coming soon)

```bash
pip install nitro-cli
```

### From Source (Development)

```bash
git clone https://github.com/nitro-sh/nitro-cli.git
cd nitro-cli
pip install -e .
```

## Quick Start

### 1. Create a New Project

```bash
nitro scaffold my-site
cd my-site
```

Choose from available templates:
- `website` - Basic website template (default)
- `portfolio` - Portfolio showcase template
- `blog` - Blog template

```bash
nitro scaffold my-portfolio --template portfolio
```

### 2. Start Development Server

```bash
nitro serve
```

Visit http://localhost:3000 to see your site.

### 3. Build for Production

```bash
nitro build
```

Your optimized site will be in the `build/` directory.

## Project Structure

When you create a new project, Nitro generates the following structure:

```
my-site/
├── nitro.config.py          # Configuration file
├── requirements.txt
├── .gitignore
├── README.md
├── src/
│   ├── components/          # Reusable YDNATL components
│   │   ├── header.py
│   │   └── footer.py
│   ├── pages/              # Page definitions (route = file path)
│   │   ├── index.py        # -> /index.html
│   │   └── about.py        # -> /about.html
│   ├── layouts/            # Page layouts/templates
│   ├── data/               # JSON/YAML data files
│   ├── styles/             # CSS stylesheets
│   ├── public/             # Static assets
│   ├── tests/              # Test files
│   └── plugins/            # Project-specific plugins
├── build/                  # Generated output
└── .nitro/                 # Nitro cache & metadata
```

## Writing Pages

Pages are Python files that return YDNATL components:

```python
# src/pages/index.py
from ydnatl import HTML, Head, Body, Div, H1, Paragraph
from nitro import Page
from components.header import Header
from components.footer import Footer

def render():
    return Page(
        title="Home",
        meta={
            "description": "Welcome to my site",
            "keywords": "static, site, generator"
        },
        content=HTML(
            Head(),
            Body(
                Header("My Website"),
                Div(
                    H1("Welcome!"),
                    Paragraph("This is built with Nitro + YDNATL!")
                ).add_class("container"),
                Footer()
            )
        )
    )
```

## Creating Components

Components are reusable YDNATL elements:

```python
# src/components/header.py
from ydnatl import Header as HTMLHeader, Nav, A, Div, H1

def Header(site_name="My Site"):
    return HTMLHeader(
        Div(
            H1(site_name).add_class("logo"),
            Nav(
                A("Home", href="/"),
                A("About", href="/about.html"),
            ).add_class("nav")
        ).add_class("header-content")
    ).add_class("header")
```

## Working with Data

Nitro provides `NitroDataStore`, a powerful and flexible way to manage JSON and YAML data in your projects.

### Quick Example

```python
# src/pages/index.py
from ydnatl import HTML, Head, Body, H1, Paragraph
from nitro import Page, load_data

def render():
    # Load data from JSON file
    data = load_data('data/site.json')

    # Access with dot notation
    return Page(
        title=data.site.name,
        content=HTML(
            Head(title=data.site.name),
            Body(
                H1(data.site.name),
                Paragraph(data.site.tagline),
                Paragraph(f"By {data.site.author}")
            )
        )
    )
```

**data/site.json:**
```json
{
  "site": {
    "name": "My Portfolio",
    "tagline": "Building amazing things",
    "author": "Alice Developer"
  }
}
```

### Multiple Access Patterns

```python
data = load_data('data/site.json')

# Dot notation (recommended for static keys)
data.site.name

# Dictionary access
data['site']['name']

# Path-based access (great for dynamic keys, with defaults)
data.get('site.name', 'Default Name')
```

### Loading from Directory

```python
# Automatically merges all JSON files in the directory
config = load_data('data/config/')
```

### See Also

For comprehensive documentation on NitroDataStore, see [docs/DATASTORE.md](docs/DATASTORE.md).

## Commands

### `nitro scaffold`

Create a new Nitro project.

```bash
nitro scaffold PROJECT_NAME [OPTIONS]

Options:
  -t, --template [website|portfolio|blog]  Template to use (default: website)
  --no-git                                 Skip git initialization
  --no-install                             Skip dependency installation
```

### `nitro generate`

Generate static HTML files from source files.

```bash
nitro generate [OPTIONS]

Options:
  -w, --watch                Watch for changes and regenerate
  -o, --output PATH          Output directory (default: build/)
  -v, --verbose              Verbose output
```

### `nitro serve`

Start a local development server with live reload.

```bash
nitro serve [OPTIONS]

Options:
  -p, --port INTEGER        Port number (default: 3000)
  -h, --host TEXT          Host address (default: localhost)
  --no-reload              Disable live reload
```

The server automatically generates the site if the build directory is empty, watches for file changes, and reloads the browser when changes are detected.

### `nitro build`

Build the site for production with optimization.

```bash
nitro build [OPTIONS]

Options:
  --minify/--no-minify     Minify HTML and CSS (default: enabled)
  --optimize/--no-optimize Optimize images and assets (default: enabled)
  -o, --output PATH        Output directory (default: build/)
  --clean                  Clean build directory before building
```

Creates an optimized production build with:
- HTML and CSS minification
- Image optimization
- Sitemap generation (sitemap.xml)
- SEO-friendly robots.txt
- Asset manifest with file hashes
- Build statistics and summary

### `nitro test`

Run quality checks on your site.

```bash
nitro test [OPTIONS]

Options:
  -c, --coverage           Generate coverage report
  -w, --watch              Watch mode
  -t, --type [all|validation|accessibility|links|performance]
```

*Coming soon!*

### `nitro docs`

Generate documentation for your site.

```bash
nitro docs [OPTIONS]

Options:
  -f, --format [html|markdown]  Output format (default: html)
  -o, --output PATH             Output directory (default: docs/)
```

*Coming soon!*

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
    }
)
```

## Plugin System

Extend Nitro with plugins. Create a plugin by extending the `NitroPlugin` class:

```python
from nitro.plugins import NitroPlugin

class MyPlugin(NitroPlugin):
    name = "my-plugin"
    version = "1.0.0"

    def on_pre_generate(self, context):
        # Called before generation
        pass

    def on_post_generate(self, context, output):
        # Called after generation, can modify output
        return output
```

Register plugins in `nitro.config.py`:

```python
config = Config(
    plugins=[
        "nitro-markdown",
        "nitro-sitemap"
    ]
)
```

## Requirements

- Python 3.8+
- YDNATL 1.0.0+

## Development

### Setting Up Development Environment

```bash
git clone https://github.com/nitro-sh/nitro-cli.git
cd nitro-cli
pip install -e .
```

### Running Tests

*Coming soon!*

```bash
pytest
```

## Roadmap

- [x] Core CLI framework
- [x] Scaffold command with templates
- [x] Generate command with YDNATL rendering
- [x] Watch mode for automatic regeneration
- [x] Serve command with hot reload
- [x] WebSocket-based live reload
- [x] Build command with optimization
- [x] HTML/CSS minification
- [x] Image optimization
- [x] Sitemap generation
- [x] NitroDataStore for flexible data management
- [ ] Test command with validators
- [ ] Docs command
- [ ] Plugin system
- [ ] Deployment integrations

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Learn More

- [YDNATL Documentation](https://github.com/sn/ydnatl)
- [Project Plan](project-plan.md)

## Support

If you encounter any issues or have questions:
- [GitHub Issues](https://github.com/nitro-sh/nitro-cli/issues)
- [Documentation](https://nitro-cli.readthedocs.io)