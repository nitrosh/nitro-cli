# My Site

A static site built with [Nitro CLI](https://github.com/nitro-sh/nitro-cli).

## Development

Start the development server with hot reload:

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

## Learn More

- [Nitro CLI](https://github.com/nitro-sh/nitro-cli) - Documentation
- [nitro-ui](https://github.com/nitrosh/nitro-ui) - HTML generation library
