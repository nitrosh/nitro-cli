# Nitro CLI - Project Plan

## Overview

Nitro is a command-line tool for scaffolding, generating, serving, building, testing, documenting, and deploying static websites. It uses [YDNATL](https://github.com/sn/ydnatl) as the rendering engine and acts as an extension to it.

**Installation:** `pip install nitro-cli`

**Python Version:** 3.8+

## Architecture

### Project Structure

```
nitro-cli/
├── pyproject.toml          # Package configuration
├── setup.py                # Setup script for pip
├── README.md
├── LICENSE
├── project-plan.md         # This file
├── src/
│   └── nitro/
│       ├── __init__.py
│       ├── cli.py          # Main CLI entry point
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── scaffold.py # Project scaffolding
│       │   ├── generate.py # HTML generation
│       │   ├── serve.py    # Dev server
│       │   ├── build.py    # Production build
│       │   ├── test.py     # Testing
│       │   └── docs.py     # Documentation generation
│       ├── core/
│       │   ├── __init__.py
│       │   ├── project.py  # Project config & management
│       │   ├── renderer.py # YDNATL integration
│       │   ├── bundler.py  # Asset bundling
│       │   └── watcher.py  # File watching for dev server
│       ├── plugins/
│       │   ├── __init__.py
│       │   ├── loader.py   # Plugin discovery & loading
│       │   └── base.py     # Plugin base class
│       ├── templates/
│       │   ├── website/    # Default website template
│       │   ├── portfolio/  # Portfolio template
│       │   └── blog/       # Blog template
│       └── utils/
│           ├── __init__.py
│           └── logger.py   # Logging utilities
├── tests/
│   ├── __init__.py
│   ├── test_commands.py
│   ├── test_renderer.py
│   └── test_plugins.py
└── docs/
    ├── getting-started.md
    ├── commands.md
    ├── plugins.md
    └── api.md
```

## Commands

### 1. `nitro scaffold [project-name] [--template=website]`

Create a new project structure with predefined templates.

**Options:**
- `--template`: Template to use (website, portfolio, blog)
- `--no-git`: Skip git initialization
- `--no-install`: Skip dependency installation

**Behavior:**
- Creates project directory structure
- Initializes git repository (optional)
- Installs dependencies
- Creates sample files based on template
- Sets up nitro.config.py

### 2. `nitro generate [--watch] [--output=build/]`

Generate static HTML files from source files.

**Options:**
- `--watch`: Watch for file changes and regenerate
- `--output`: Output directory (default: build/)
- `--verbose`: Verbose logging

**Behavior:**
- Scans `src/pages/` for Python files
- Executes Python files to generate YDNATL components
- Renders to HTML with proper routing
- Processes data from `src/data/`
- Injects styles from `src/styles/`
- Copies public assets
- Supports incremental builds

### 3. `nitro serve [--port=3000] [--host=localhost]`

Start a local development server to preview the static site.

**Options:**
- `--port`: Port number (default: 3000)
- `--host`: Host address (default: localhost)
- `--no-reload`: Disable live reload

**Behavior:**
- Runs local dev server with hot reload
- Watches for file changes
- Auto-regenerates on changes
- Serves from `build/` directory
- Provides live reload via WebSockets

### 4. `nitro build [--minify] [--optimize]`

Bundle and optimize the static site for production.

**Options:**
- `--minify`: Minify HTML and CSS (default: true)
- `--optimize`: Optimize images and assets (default: true)
- `--output`: Output directory (default: build/)

**Behavior:**
- Production-ready build
- Minifies HTML/CSS/JS
- Optimizes images
- Generates sitemap
- Creates asset manifest
- Tree-shaking for unused code

### 5. `nitro test [--coverage] [--watch]`

Run tests on the static site to ensure quality.

**Options:**
- `--coverage`: Generate coverage report
- `--watch`: Watch mode for continuous testing
- `--type`: Test type (all, validation, accessibility, links, performance)

**Behavior:**
- Runs tests from `src/tests/`
- HTML validation (HTML5)
- Accessibility checks (WCAG)
- Link checking (broken links)
- Performance audits
- Visual regression tests (optional)

### 6. `nitro docs [--format=html]`

Generate documentation for the static site.

**Options:**
- `--format`: Output format (html, markdown)
- `--output`: Output directory (default: docs/)

**Behavior:**
- Generates component documentation
- Auto-documents page structure
- Creates style guide
- Exports to various formats

## User Project Structure

When a user runs `nitro scaffold my-site`, the following structure is created:

```
my-site/
├── nitro.config.py          # Configuration file
├── requirements.txt
├── .gitignore
├── README.md
├── src/
│   ├── components/          # Reusable YDNATL components
│   │   ├── __init__.py
│   │   ├── header.py
│   │   ├── footer.py
│   │   └── navigation.py
│   ├── pages/              # Page definitions (route = file path)
│   │   ├── __init__.py
│   │   ├── index.py        # -> /index.html
│   │   ├── about.py        # -> /about.html
│   │   └── blog/
│   │       ├── __init__.py
│   │       └── post.py     # -> /blog/post.html
│   ├── layouts/            # Page layouts/templates
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── blog.py
│   ├── data/               # JSON/YAML/CSV data files
│   │   ├── site.json
│   │   └── posts.json
│   ├── styles/             # CSS/SCSS files
│   │   ├── main.css
│   │   └── themes/
│   ├── public/             # Static assets
│   │   ├── images/
│   │   ├── fonts/
│   │   └── favicon.ico
│   ├── tests/              # Test files
│   │   ├── test_pages.py
│   │   └── test_components.py
│   └── plugins/            # Project-specific plugins
│       └── custom_plugin.py
├── build/                  # Generated output
│   ├── index.html
│   ├── about.html
│   ├── assets/
│   │   ├── css/
│   │   └── js/
│   └── images/
└── .nitro/                 # Nitro cache & metadata
    ├── cache/
    └── manifest.json
```

## Configuration System

### nitro.config.py

Users can configure Nitro via a Python configuration file:

```python
from nitro import Config

config = Config(
    # Site metadata
    site_name="My Site",
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

    # Plugins
    plugins=[
        "nitro-markdown",
        "nitro-sitemap",
        "nitro-rss"
    ],

    # Custom metadata
    metadata={
        "author": "Your Name",
        "description": "Site description",
        "keywords": ["static", "site", "generator"]
    }
)
```

## Plugin System

### Plugin Architecture

Plugins extend Nitro's functionality through a hook-based system.

**Base Plugin Class:**

```python
# src/nitro/plugins/base.py
class NitroPlugin:
    """Base class for all Nitro plugins"""

    name: str
    version: str

    def on_init(self, config):
        """Called when plugin is loaded"""
        pass

    def on_pre_generate(self, context):
        """Before HTML generation"""
        pass

    def on_post_generate(self, context, output):
        """After HTML generation, can modify output"""
        return output

    def on_pre_build(self, context):
        """Before production build"""
        pass

    def on_post_build(self, context):
        """After production build"""
        pass

    def add_commands(self, cli):
        """Add custom CLI commands"""
        pass

    def process_data(self, data_file, content):
        """Process data files (e.g., markdown -> JSON)"""
        return content
```

**Example Plugin:**

```python
# Example: Markdown plugin
from nitro.plugins import NitroPlugin
import markdown

class MarkdownPlugin(NitroPlugin):
    name = "nitro-markdown"
    version = "1.0.0"

    def process_data(self, data_file, content):
        if data_file.endswith('.md'):
            return markdown.markdown(content)
        return content

    def on_post_generate(self, context, output):
        # Could add TOC, syntax highlighting, etc.
        return output
```

### Plugin Discovery

Plugins can be:
1. Installed via pip (`pip install nitro-markdown`)
2. Placed in user's `src/plugins/` directory
3. Registered in `nitro.config.py`

## YDNATL Integration

### Page Definition Pattern

Pages are Python files that return YDNATL components:

```python
# src/pages/index.py
from ydnatl import HTML, Head, Body, Div, H1, Paragraph
from src.components.header import Header
from src.components.footer import Footer
from nitro import Page, load_data

# Load data
site_data = load_data('data/site.json')

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
                Header(site_name=site_data['name']),
                Div(
                    H1("Welcome to my site"),
                    Paragraph("This is built with Nitro + YDNATL!")
                ).add_class("container"),
                Footer()
            )
        )
    )
```

### Component Pattern

Reusable components:

```python
# src/components/header.py
from ydnatl import Header as HTMLHeader, Nav, A, Div

def Header(site_name="My Site"):
    return HTMLHeader(
        Div(
            site_name
        ).add_class("logo"),
        Nav(
            A("Home", href="/"),
            A("About", href="/about"),
            A("Blog", href="/blog")
        ).add_class("nav")
    ).add_class("header")
```

## Dependencies

### Core Dependencies

```
click>=8.0.0              # CLI framework
ydnatl>=1.0.0            # HTML rendering engine
watchdog>=2.1.0          # File system monitoring for serve command
rich>=10.0.0             # Beautiful CLI output and logging
pyyaml>=6.0              # YAML data file support
aiohttp>=3.8.0           # Async HTTP server with WebSocket support
aiofiles>=0.8.0          # Async file operations
```

### Build & Optimization

```
csscompressor>=0.9.5     # CSS minification
htmlmin>=0.1.12          # HTML minification
pillow>=9.0.0            # Image optimization
```

### Testing (dev dependency)

```
pytest>=7.0.0            # Testing framework
html5lib>=1.1            # HTML5 validation
beautifulsoup4>=4.11.0   # HTML parsing for tests
```

### Optional

```
python-frontmatter>=1.0.0  # For markdown files with frontmatter
markdown>=3.3.0            # Markdown support (for blog posts)
```

## Implementation Roadmap

### Phase 1: Core Foundation (Week 1-2)

**Priority: HIGH**

- [ ] Set up project structure
- [ ] Create pyproject.toml and setup.py
- [ ] Implement CLI framework with Click
- [ ] Create entry point for pip installation
- [ ] Create basic `scaffold` command
- [ ] Integrate YDNATL renderer
- [ ] Implement simple `generate` command

**Deliverables:**
- Working `nitro scaffold` command
- Basic `nitro generate` command
- Installable via pip in development mode

### Phase 2: Development Experience (Week 3-4)

**Priority: HIGH**

- [ ] Implement `serve` command with aiohttp
- [ ] Add file watching with watchdog
- [ ] Implement hot reload with WebSockets
- [ ] Create configuration system
- [ ] Add rich logging and error handling
- [ ] Create "website" template
- [ ] Create "portfolio" template
- [ ] Create "blog" template

**Deliverables:**
- Working dev server with hot reload
- Three project templates
- Configuration system

### Phase 3: Build & Optimization (Week 5-6)

**Priority: HIGH**

- [ ] Implement `build` command
- [ ] Add HTML minification
- [ ] Add CSS minification
- [ ] Implement asset bundling
- [ ] Add image optimization (optional)
- [ ] Create cache system for incremental builds
- [ ] Generate asset manifest

**Deliverables:**
- Production-ready build command
- Optimized output

### Phase 4: Testing & Documentation (Week 7-8)

**Priority: MEDIUM**

- [ ] Implement `test` command
- [ ] Add HTML5 validation
- [ ] Implement link checking
- [ ] Add accessibility checks
- [ ] Implement `docs` command
- [ ] Create comprehensive user documentation
- [ ] Write API documentation

**Deliverables:**
- Working test suite
- Documentation generation
- User guides

### Phase 5: Plugin System (Week 9-10)

**Priority: MEDIUM**

- [ ] Design and implement plugin architecture
- [ ] Create plugin loader with discovery
- [ ] Implement plugin hooks
- [ ] Build example plugins:
  - [ ] Markdown plugin
  - [ ] Sitemap plugin
  - [ ] RSS feed plugin
- [ ] Document plugin API
- [ ] Create plugin development guide

**Deliverables:**
- Working plugin system
- Example plugins
- Plugin documentation

### Phase 6: Polish & Release (Week 11-12)

**Priority: HIGH**

- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] Error handling improvements
- [ ] User documentation
- [ ] Contributing guidelines
- [ ] Prepare for PyPI release
- [ ] Create release pipeline

**Deliverables:**
- Production-ready 1.0.0 release
- Published to PyPI
- Complete documentation

## Installation & Distribution

### Package Configuration

The project will use modern Python packaging:

**pyproject.toml:**
```toml
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "nitro-cli"
version = "1.0.0"
description = "A CLI tool for building static websites with YDNATL"
authors = [{name = "Your Name", email = "your.email@example.com"}]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
dependencies = [
    "click>=8.0.0",
    "ydnatl>=1.0.0",
    "watchdog>=2.1.0",
    "rich>=10.0.0",
    "pyyaml>=6.0",
    "aiohttp>=3.8.0",
    "aiofiles>=0.8.0",
    "csscompressor>=0.9.5",
    "htmlmin>=0.1.12",
    "pillow>=9.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "html5lib>=1.1",
    "beautifulsoup4>=4.11.0",
]
markdown = [
    "python-frontmatter>=1.0.0",
    "markdown>=3.3.0",
]

[project.scripts]
nitro = "nitro.cli:main"

[project.urls]
Homepage = "https://github.com/yourusername/nitro-cli"
Documentation = "https://nitro-cli.readthedocs.io"
Repository = "https://github.com/yourusername/nitro-cli"
```

### Installation Methods

**From PyPI (after release):**
```bash
pip install nitro-cli
```

**From source (development):**
```bash
git clone https://github.com/yourusername/nitro-cli.git
cd nitro-cli
pip install -e .
```

**With optional dependencies:**
```bash
pip install nitro-cli[markdown]
```

## Future Enhancements

### Planned Features

1. **Hot Module Replacement (HMR)** - Fast refresh during development
2. **Asset Pipeline** - Automatic CSS preprocessing (SCSS, PostCSS)
3. **Image Optimization** - Auto-resize and compress images
4. **SEO Tools** - Enhanced sitemap, robots.txt, meta tag management
5. **Deployment Integration** - Deploy to custom hosting platform
6. **Theming System** - Multiple theme support with YDNATL's built-in themes
7. **Component Library** - Pre-built components (cards, forms, etc.)
8. **Data Sources** - Support for external APIs, headless CMS
9. **Incremental Builds** - Enhanced caching and build optimization
10. **TypeScript/JSDoc** - Type hints for better developer experience

### Community

- GitHub repository for issues and contributions
- Documentation site
- Example projects
- Video tutorials
- Community plugins

## Success Metrics

- Installation via pip works seamlessly
- All commands function as documented
- Build performance (< 1s for small sites)
- Clear error messages
- Comprehensive documentation
- Active community engagement

## Notes

- Focus on efficient static site generation
- Keep the core lightweight
- Prioritize developer experience
- Build for extensibility via plugins
- Prepare for future hosting platform integration