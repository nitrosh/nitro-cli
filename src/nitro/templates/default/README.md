# My Site

A static site built with [Nitro CLI](https://github.com/nitro-sh/nitro-cli).

## Development

Start the development server with hot-reload:

```bash
nitro dev
```

Your site will be available at http://localhost:3000

## Building

Build for production:

```bash
nitro build
```

Preview the production build:

```bash
nitro preview
```

## Project Structure

```
├── src/
│   ├── pages/          # Page files (route = file path)
│   ├── components/     # Reusable components
│   ├── styles/         # CSS stylesheets
│   └── data/           # JSON/YAML data
├── build/              # Generated output
└── nitro.config.py     # Configuration
```

## Ecosystem

Nitro isn’t just one library - it's a growing toolkit of focused building blocks you can mix and match to ship faster:

- **[nitro-ui](https://github.com/nitrosh/nitro-ui)** - Generate clean, reusable HTML with a lightweight, developer-friendly API
- **[nitro-datastore](https://github.com/nitrosh/nitro-datastore)** - Load and access data effortlessly using simple dot-notation paths
- **[nitro-dispatch](https://github.com/nitrosh/nitro-dispatch)** - A flexible plugin system to extend features without touching core code
- **[nitro-validate](https://github.com/nitrosh/nitro-validate)** - Fast, reliable data validation to keep your inputs and payloads rock-solid
