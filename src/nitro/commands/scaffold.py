"""Scaffold command for creating new Nitro projects."""

import shutil
import subprocess
import sys
from pathlib import Path

import click
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..utils import logger, LogLevel, info, warning, verbose, configure


@click.command()
@click.argument("project_name")
@click.option(
    "--template",
    "-t",
    type=click.Choice(["website", "portfolio", "blog"], case_sensitive=False),
    default="website",
    help="Template to use for the project",
)
@click.option("--no-git", is_flag=True, help="Skip git initialization")
@click.option("--no-install", is_flag=True, help="Skip dependency installation")
@click.option(
    "--verbose", "-v", "verbose_flag", is_flag=True, help="Enable verbose output"
)
@click.option("--debug", is_flag=True, help="Enable debug mode with full tracebacks")
@click.option("--log-file", type=click.Path(), help="Write logs to a file")
def scaffold(project_name, template, no_git, no_install, verbose_flag, debug, log_file):
    """
    Create a new Nitro project.

    PROJECT_NAME: Name of the project directory to create
    """
    # Configure logging
    if debug:
        configure(level=LogLevel.DEBUG, log_file=log_file)
    elif verbose_flag:
        configure(level=LogLevel.VERBOSE, log_file=log_file)
    elif log_file:
        configure(log_file=log_file)

    try:
        # Show banner
        logger.banner("Project Scaffold")
        logger.start_timer()

        project_path = Path.cwd() / project_name

        # Check if directory already exists
        if project_path.exists():
            logger.error_panel(
                "Directory Exists",
                f"Directory '{project_name}' already exists!",
                hint="Choose a different project name or remove the existing directory",
            )
            sys.exit(1)

        info(f"Creating new Nitro project: {project_name}")
        verbose(f"Template: {template}")
        verbose(f"Location: {project_path}")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=logger.console,
        ) as progress:
            # Create project directory
            task = progress.add_task("Creating project structure...", total=None)
            project_path.mkdir(parents=True)
            verbose(f"Created directory: {project_path}")

            # Copy template
            progress.update(task, description="Copying template files...")
            template_path = Path(__file__).parent.parent / "templates" / template
            file_count = copy_template(template_path, project_path, verbose_flag)
            verbose(f"Copied {file_count} template files")

            # Create additional directories
            progress.update(task, description="Creating directories...")
            (project_path / "build").mkdir(exist_ok=True)
            (project_path / ".nitro" / "cache").mkdir(parents=True, exist_ok=True)
            verbose("Created build/ and .nitro/cache/ directories")

            # Create requirements.txt
            progress.update(task, description="Creating requirements.txt...")
            create_requirements_txt(project_path)
            verbose("Created requirements.txt")

            # Create .gitignore
            progress.update(task, description="Creating .gitignore...")
            create_gitignore(project_path)
            verbose("Created .gitignore")

            # Initialize git
            if not no_git:
                progress.update(task, description="Initializing git repository...")
                try:
                    subprocess.run(
                        ["git", "init"],
                        cwd=project_path,
                        check=True,
                        capture_output=True,
                    )
                    verbose("Initialized git repository")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    warning("Git initialization failed (is git installed?)")

            # Install dependencies
            if not no_install:
                progress.update(task, description="Installing dependencies...")
                try:
                    subprocess.run(
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
                    )
                    verbose("Dependencies installed successfully")
                except subprocess.CalledProcessError:
                    warning(
                        "Failed to install dependencies. Install manually with: pip install -r requirements.txt"
                    )

            progress.remove_task(task)

        # Show completion panel
        logger.newline()
        logger.scaffold_complete(project_name, template)

    except Exception as e:
        if debug:
            logger.exception(e, show_trace=True)
        else:
            logger.error_panel(
                "Scaffold Error", str(e), hint="Use --debug for full traceback"
            )
        sys.exit(1)


def copy_template(src: Path, dst: Path, verbose_mode: bool = False) -> int:
    """
    Copy template directory to destination.

    Args:
        src: Source template directory
        dst: Destination project directory
        verbose_mode: Whether to log each file

    Returns:
        Number of files copied
    """
    if not src.exists():
        raise FileNotFoundError(f"Template not found: {src}")

    count = 0
    for item in src.rglob("*"):
        if item.is_file():
            relative = item.relative_to(src)
            dest_file = dst / relative
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest_file)
            count += 1
            if verbose_mode:
                verbose(f"  {relative}")

    return count


def create_requirements_txt(project_path: Path) -> None:
    """
    Create requirements.txt file.

    Args:
        project_path: Path to project directory
    """
    requirements = """# Core dependencies
nitro-cli>=0.1.0
nitro-ui>=0.1.0
nitro-datastore>=0.1.0

# Optional dependencies
# markdown>=3.3.0  # For markdown support
# python-frontmatter>=1.0.0  # For frontmatter parsing
"""
    (project_path / "requirements.txt").write_text(requirements)


def create_gitignore(project_path: Path) -> None:
    """Create .gitignore file.

    Args:
        project_path: Path to project directory
    """
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
