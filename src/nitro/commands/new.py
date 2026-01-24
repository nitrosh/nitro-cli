"""Command for creating new Nitro projects."""

import shutil
import subprocess
import sys
from pathlib import Path

import click
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..utils import (
    LogLevel,
    set_level,
    console,
    warning,
    verbose,
    header,
    error_panel,
    project_created,
)


@click.command()
@click.argument("project_name")
@click.option("--no-git", is_flag=True, help="Skip git initialization")
@click.option("--no-install", is_flag=True, help="Skip dependency installation")
@click.option(
    "--verbose", "-v", "verbose_flag", is_flag=True, help="Enable verbose output"
)
@click.option("--debug", is_flag=True, help="Enable debug mode with full tracebacks")
def new(project_name, no_git, no_install, verbose_flag, debug):
    """Create a new Nitro project."""
    if debug:
        set_level(LogLevel.DEBUG)
    elif verbose_flag:
        set_level(LogLevel.VERBOSE)

    try:
        header(f"Creating {project_name}...")

        project_path = Path.cwd() / project_name

        if project_path.exists():
            error_panel(
                "Directory Exists",
                f"Directory '{project_name}' already exists!",
                hint="Choose a different project name or remove the existing directory",
            )
            sys.exit(1)

        verbose(f"Location: {project_path}")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("Creating project structure...", total=None)
            project_path.mkdir(parents=True)
            verbose(f"Created directory: {project_path}")

            progress.update(task, description="Copying template files...")
            template_path = Path(__file__).parent.parent / "templates" / "default"
            file_count = copy_template(template_path, project_path, verbose_flag)
            verbose(f"Copied {file_count} template files")

            progress.update(task, description="Creating directories...")
            (project_path / "build").mkdir(exist_ok=True)
            (project_path / ".nitro" / "cache").mkdir(parents=True, exist_ok=True)
            verbose("Created build/ and .nitro/cache/ directories")

            progress.update(task, description="Creating requirements.txt...")
            create_requirements_txt(project_path)
            verbose("Created requirements.txt")

            progress.update(task, description="Creating .gitignore...")
            create_gitignore(project_path)
            verbose("Created .gitignore")

            if not no_git:
                progress.update(task, description="Initializing git repository...")
                try:
                    result = subprocess.run(
                        ["git", "init"],
                        cwd=project_path,
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    verbose("Initialized git repository")
                    if verbose_flag and result.stdout:
                        verbose(f"  {result.stdout.strip()}")
                except subprocess.CalledProcessError as e:
                    warning(f"Git initialization failed: {e.stderr or e}")
                except FileNotFoundError:
                    warning("Git initialization failed (is git installed?)")

            if not no_install:
                progress.update(task, description="Installing dependencies...")
                try:
                    result = subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            "pip",
                            "install",
                            "-r",
                            "requirements.txt",
                        ],
                        cwd=project_path,
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    verbose("Dependencies installed successfully")
                    if verbose_flag and result.stdout:
                        lines = result.stdout.strip().split("\n")
                        for line in lines[-3:]:
                            if line.strip():
                                verbose(f"  {line.strip()}")
                except subprocess.CalledProcessError as e:
                    error_msg = e.stderr or str(e)
                    warning(
                        f"Failed to install dependencies: {error_msg[:100]}..."
                        if len(error_msg) > 100
                        else f"Failed to install dependencies: {error_msg}"
                    )
                    warning("Install manually with: pip install -r requirements.txt")

        project_created(project_name)

    except Exception as e:
        error_panel("Scaffold Error", str(e), hint="Use --debug for full traceback")
        sys.exit(1)


def copy_template(src: Path, dst: Path, verbose_mode: bool = False) -> int:
    """Copy template directory to destination."""
    if not src.exists():
        raise FileNotFoundError(f"Template not found: {src}")

    count = 0
    for item in src.rglob("*"):
        if item.is_file():
            relative = item.relative_to(src)
            dest_file = dst / relative
            try:
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest_file)
                count += 1
                if verbose_mode:
                    verbose(f"  {relative}")
            except PermissionError as e:
                raise OSError(f"Permission denied copying {relative}: {e}") from e
            except OSError as e:
                raise OSError(f"Failed to copy {relative}: {e}") from e

    return count


def create_requirements_txt(project_path: Path) -> None:
    """Create requirements.txt file."""
    requirements = """# Core dependencies
nitro-cli>=0.1.0
nitro-ui>=1.0.3
nitro-datastore>=1.0.0

# Optional dependencies
# markdown>=3.3.0  # For markdown support
# python-frontmatter>=1.0.0  # For frontmatter parsing
"""
    (project_path / "requirements.txt").write_text(requirements)


def create_gitignore(project_path: Path) -> None:
    """Create .gitignore file."""
    gitignore = """# Nitro
build/
.nitro/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
"""
    (project_path / ".gitignore").write_text(gitignore)
