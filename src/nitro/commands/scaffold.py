"""Scaffold command for creating new Nitro projects."""

import shutil
from pathlib import Path

import click
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..utils import success, error, info


@click.command()
@click.argument("project_name")
@click.option(
    "--template",
    "-t",
    type=click.Choice(["website", "portfolio", "blog"], case_sensitive=False),
    default="website",
    help="Template to use for the project",
)
@click.option(
    "--no-git",
    is_flag=True,
    help="Skip git initialization"
)
@click.option(
    "--no-install",
    is_flag=True,
    help="Skip dependency installation"
)
def scaffold(project_name, template, no_git, no_install):
    """
    Create a new Nitro project.

    PROJECT_NAME: Name of the project directory to create
    """
    import subprocess
    import sys

    project_path = Path.cwd() / project_name

    # Check if directory already exists
    if project_path.exists():
        error(f"Directory '{project_name}' already exists!")
        sys.exit(1)

    info(f"Creating new Nitro project: {project_name}")
    info(f"Using template: {template}")

    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
    ) as progress:
        # Create project directory
        task = progress.add_task("Creating project structure...", total=None)
        project_path.mkdir(parents=True)

        # Copy template
        progress.update(task, description="Copying template files...")
        template_path = Path(__file__).parent.parent / "templates" / template
        copy_template(template_path, project_path)

        # Create additional directories
        progress.update(task, description="Creating directories...")
        (project_path / "build").mkdir(exist_ok=True)
        (project_path / ".nitro" / "cache").mkdir(parents=True, exist_ok=True)

        # Create requirements.txt
        progress.update(task, description="Creating requirements.txt...")
        create_requirements_txt(project_path)

        # Create .gitignore
        progress.update(task, description="Creating .gitignore...")
        create_gitignore(project_path)

        # Initialize git
        if not no_git:
            progress.update(task, description="Initializing git repository...")
            try:
                subprocess.run(
                    ["git", "init"], cwd=project_path, check=True, capture_output=True
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                error("Git initialization failed (is git installed?)")

        # Install dependencies
        if not no_install:
            progress.update(task, description="Installing dependencies...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                    cwd=project_path,
                    check=True,
                    capture_output=True,
                )
            except subprocess.CalledProcessError:
                error(
                    "Failed to install dependencies. You can install them manually with: pip install -r requirements.txt"
                )

        progress.remove_task(task)

    success(f"Project '{project_name}' created successfully!")
    info(f"\nTo get started:")
    info(f"  cd {project_name}")
    info(f"  nitro serve")


def copy_template(src: Path, dst: Path) -> None:
    """
    Copy template directory to destination.

    Args:
        src: Source template directory
        dst: Destination project directory
    """
    if not src.exists():
        error(f"Template not found: {src}")
        return

    for item in src.rglob("*"):
        if item.is_file():
            relative = item.relative_to(src)
            dest_file = dst / relative
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest_file)


def create_requirements_txt(project_path: Path) -> None:
    """
    Create requirements.txt file.

    Args:
        project_path: Path to project directory
    """
    requirements = """# Core dependencies
ydnatl>=1.0.0

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
