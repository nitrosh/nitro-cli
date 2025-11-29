# Nitro CLI

> A powerful static site generator built with Python

Nitro CLI is a command-line tool that helps you build beautiful static websites using Python and [nitro-ui](https://github.com/nitrosh/nitro-ui). Write your pages in Python, leverage the power of nitro-ui's HTML builder, and deploy static sites with ease.

## Features

- **Python-Powered**: Write pages using Python and nitro-ui instead of template languages
- **Component-Based**: Reusable components with a clean architecture
- **Fast Development**: Built-in development server with hot reload
- **Production Ready**: Optimized builds with minification and asset optimization
- **Flexible Data**: Load JSON/YAML data with [nitro-datastore](https://github.com/nitrosh/nitro-datastore)
- **Extensible**: Plugin system powered by [nitro-dispatch](https://github.com/nitrosh/nitro-dispatch)
- **Multiple Templates**: Start quickly with website, portfolio, or blog templates

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

Choose from available templates:
- `website` - Basic website template (default)
- `portfolio` - Portfolio showcase template
- `blog` - Blog template

```bash
nitro new my-portfolio --template portfolio
```

### 2. Start Development Server

```bash
nitro serve
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
│   │   └── about.py        # -> /about.html
│   ├── data/               # JSON/YAML data files
│   ├── styles/             # CSS stylesheets
│   ├── public/             # Static assets (copied to build root)
│   └── plugins/            # Project-specific plugins
├── build/                  # Generated output
└── .nitro/                 # Nitro cache & metadata
```

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

## Creating Components

Components are reusable nitro-ui elements:

```python
# src/components/header.py
from nitro_ui import Header as UIHeader, Nav, HtmlLink, Div, H1

def Header(site_name="My Site"):
    logo = H1(site_name)
    logo.add_attribute("class", "logo")

    nav = Nav(
        HtmlLink("Home", href="/"),
        HtmlLink("About", href="/about.html"),
    )
    nav.add_attribute("class", "nav")

    header_content = Div(logo, nav)
    header_content.add_attribute("class", "header-content")

    header = UIHeader(header_content)
    header.add_attribute("class", "header")

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

## Commands

### `nitro new`

Create a new Nitro project.

```bash
nitro new PROJECT_NAME [OPTIONS]

Options:
  -t, --template [website|portfolio|blog]  Template to use (default: website)
  --no-git                                 Skip git initialization
  --no-install                             Skip dependency installation
  -v, --verbose                            Enable verbose output
  --debug                                  Enable debug mode with full tracebacks
  --log-file PATH                          Write logs to a file
```

### `nitro serve`

Start a local development server with live reload.

```bash
nitro serve [OPTIONS]

Options:
  -p, --port INTEGER        Port number (default: 3000)
  -h, --host TEXT          Host address (default: localhost)
  --no-reload              Disable live reload
  -v, --verbose            Enable verbose output
  --debug                  Enable debug mode with full tracebacks
  --log-file PATH          Write logs to a file
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
  -v, --verbose            Enable verbose output
  -q, --quiet              Only show errors and final summary
  --debug                  Enable debug mode with full tracebacks
  --log-file PATH          Write logs to a file
```

Creates an optimized production build with:
- HTML and CSS minification
- Image optimization
- Sitemap generation (sitemap.xml)
- SEO-friendly robots.txt
- Asset manifest with file hashes
- Build statistics and summary

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
# src/plugins/my_plugin.py
from nitro.plugins import NitroPlugin, hook

class MyPlugin(NitroPlugin):
    name = "my-plugin"
    version = "1.0.0"

    @hook("nitro.pre_build")
    def on_pre_build(self, context):
        # Called before build starts
        print(f"Building to {context['build_dir']}")

    @hook("nitro.post_build")
    def on_post_build(self, context):
        # Called after build completes
        print(f"Build complete! {context['stats']['count']} files generated")
```

Available hooks:
- `nitro.init` - Plugin initialization
- `nitro.pre_generate` - Before page generation
- `nitro.post_generate` - After page generation (can modify output)
- `nitro.pre_build` - Before production build
- `nitro.post_build` - After production build

Register plugins in `nitro.config.py`:

```python
config = Config(
    plugins=[
        "my_plugin.MyPlugin",
    ]
)
```

## Requirements

- Python 3.8+
- nitro-ui
- nitro-datastore
- nitro-dispatch

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
