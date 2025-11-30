# Development Guide

This guide covers how to set up Nitro CLI for local development and testing.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- git

## Setting Up Development Environment

### 1. Clone the Repository

```bash
git clone https://github.com/nitro-sh/nitro-cli.git
cd nitro-cli
```

### 2. Create a Virtual Environment (Recommended)

Using a virtual environment isolates your development dependencies from your system Python installation.

**On macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**On Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

You should see `(.venv)` in your terminal prompt when the virtual environment is activated.

### 3. Install in Development Mode

Install the package in **editable mode** (also called development mode) using pip:

```bash
pip install -e .
```

**What does `-e` (editable mode) do?**
- Installs the package without copying files
- Links directly to your source code
- Changes to the code are immediately available without reinstalling
- Perfect for development and testing

### 4. Verify Installation

Test that the `nitro` command is available:

```bash
nitro --version
```

You should see:
```
nitro, version 0.1.0
```

Check available commands:
```bash
nitro --help
```

## Development Workflow

### Making Changes

1. **Edit the source code** in `src/nitro/`
2. **Test immediately** - Your changes are live due to editable mode
3. **No reinstallation needed** - Just run `nitro` commands

Example:
```bash
# Edit a file
vim src/nitro/commands/scaffold.py

# Test immediately
nitro scaffold test-project
```

### Installing Optional Dependencies

Install development dependencies:

```bash
pip install -e ".[dev]"
```

This includes:
- pytest (testing framework)
- html5lib (HTML validation)
- beautifulsoup4 (HTML parsing)
- black (code formatter)
- flake8 (linter)

Install markdown support:

```bash
pip install -e ".[markdown]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

Format code with black:

```bash
black src/
```

Lint code with flake8:

```bash
flake8 src/
```

## Testing Your Changes

### Test with a Fresh Project

1. Create a test project in a temporary directory:

```bash
cd /tmp
nitro scaffold test-site --no-git --no-install
cd test-site
```

2. Test the commands:

```bash
# Generate the site
nitro generate

# Start dev server (Ctrl+C to stop)
nitro serve

# Build for production
nitro build
```

3. Clean up:

```bash
cd ..
rm -rf test-site
```

### Test Different Templates

```bash
nitro scaffold test-website --template website
nitro scaffold test-portfolio --template portfolio
nitro scaffold test-blog --template blog
```

## Troubleshooting

### Command Not Found

If `nitro` command is not found after installation:

1. **Check your PATH:**
   ```bash
   echo $PATH
   ```

2. **Find where pip installed the command:**
   ```bash
   which nitro  # macOS/Linux
   where nitro  # Windows
   ```

3. **Try running with python -m:**
   ```bash
   python -m nitro --version
   ```

4. **Reinstall in editable mode:**
   ```bash
   pip uninstall nitro-cli
   pip install -e .
   ```

### Import Errors

If you see import errors:

1. **Verify you're in the virtual environment:**
   ```bash
   which python  # Should show .venv/bin/python
   ```

2. **Reinstall dependencies:**
   ```bash
   pip install -e .
   ```

3. **Check your Python version:**
   ```bash
   python --version  # Should be 3.8 or higher
   ```

### Changes Not Reflected

If your code changes aren't showing up:

1. **Verify editable mode is active:**
   ```bash
   pip show nitro-cli
   ```
   Should show: `Editable project location: /path/to/nitro-cli`

2. **Check for syntax errors:**
   ```bash
   python -m py_compile src/nitro/commands/scaffold.py
   ```

3. **Restart Python if testing in interactive mode:**
   ```python
   # In Python REPL, changes require restart
   exit()
   python
   ```

### Virtual Environment Issues

If you have problems with the virtual environment:

1. **Deactivate and reactivate:**
   ```bash
   deactivate
   source .venv/bin/activate  # macOS/Linux
   .venv\Scripts\activate     # Windows
   ```

2. **Recreate the virtual environment:**
   ```bash
   deactivate
   rm -rf .venv
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

## Project Structure for Development

```
nitro-cli/
├── src/nitro/              # Main package source
│   ├── __init__.py
│   ├── cli.py             # CLI entry point
│   ├── commands/          # Command implementations
│   ├── core/              # Core functionality
│   ├── plugins/           # Plugin system
│   ├── templates/         # Project templates
│   └── utils/             # Utilities
├── tests/                  # Test suite
├── docs/                   # Documentation
├── pyproject.toml         # Package configuration
├── setup.py               # Setup script
├── README.md              # Main documentation
└── DEVELOPMENT.md         # This file
```

## Adding New Commands

To add a new command:

1. **Create command file:**
   ```bash
   touch src/nitro/commands/mycommand.py
   ```

2. **Implement the command:**
   ```python
   """My command description."""
   import click

   @click.command()
   def mycommand():
       """My command help text."""
       print("Hello from mycommand!")
   ```

3. **Register in `commands/__init__.py`:**
   ```python
   from .mycommand import mycommand
   __all__ = [..., "mycommand"]
   ```

4. **Register in `cli.py`:**
   ```python
   from .commands import mycommand
   main.add_command(mycommand)
   ```

5. **Test immediately:**
   ```bash
   nitro mycommand
   ```

## Updating Dependencies

To add a new dependency:

1. **Add to `pyproject.toml`:**
   ```toml
   dependencies = [
       "existing-package>=1.0.0",
       "new-package>=2.0.0",  # Add here
   ]
   ```

2. **Reinstall:**
   ```bash
   pip install -e .
   ```

## Building for Distribution

### Build Source and Wheel Distributions

```bash
# Install build tools
pip install build

# Build distributions
python -m build
```

This creates:
- `dist/nitro_cli-0.1.0.tar.gz` (source distribution)
- `dist/nitro_cli-0.1.0-py3-none-any.whl` (wheel distribution)

### Test the Built Package

```bash
# Create a fresh virtual environment
python3 -m venv test-env
source test-env/bin/activate

# Install from wheel
pip install dist/nitro_cli-0.1.0-py3-none-any.whl

# Test
nitro --version

# Clean up
deactivate
rm -rf test-env
```

## Publishing to PyPI

### Test PyPI (for testing)

```bash
# Install twine
pip install twine

# Upload to Test PyPI
python -m twine upload --repository testpypi dist/*

# Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ nitro-cli
```

### Production PyPI

```bash
# Upload to PyPI
python -m twine upload dist/*
```

## Getting Help

- **GitHub Issues:** https://github.com/nitro-sh/nitro-cli/issues
- **Documentation:** https://nitro-cli.readthedocs.io
- **Project Plan:** See [project-plan.md](project-plan.md)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Tips for Development

1. **Use verbose mode** when testing commands:
   ```bash
   nitro generate --verbose
   ```

2. **Check logs** in the `.nitro/` directory of test projects

3. **Test with different templates** to ensure compatibility

4. **Test on different operating systems** if possible (Linux, macOS, Windows)

5. **Keep your virtual environment clean** - recreate it periodically

6. **Use git branches** for different features

7. **Write tests** for new functionality

8. **Update documentation** when adding features

## Quick Reference

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# Test
nitro --version
nitro --help

# Develop
# (Edit files in src/nitro/)
nitro <command>  # Test immediately

# Clean up
deactivate
```

## Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [Click Documentation](https://click.palletsprojects.com/)
- [nitro-ui Documentation](https://github.com/nitro-sh/nitro-ui)
- [Rich Documentation](https://rich.readthedocs.io/)