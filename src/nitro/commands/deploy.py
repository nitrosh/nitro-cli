"""Deploy command for one-click deployments."""

import subprocess
import shutil
import sys
from pathlib import Path

import click

from ..core.config import load_config
from ..core.project import get_project_root
from ..utils import logger, info, success, error


@click.command()
@click.option(
    "--platform",
    "-p",
    type=click.Choice(
        ["auto", "netlify", "vercel", "cloudflare"], case_sensitive=False
    ),
    default="auto",
    help="Deployment platform (auto-detect if not specified)",
)
@click.option("--build/--no-build", default=True, help="Build before deploying")
@click.option("--prod", is_flag=True, help="Deploy to production (not preview)")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def deploy(platform, build, prod, verbose):
    """
    Deploy the site to a hosting platform.

    Supports Netlify, Vercel, and Cloudflare Pages.
    Auto-detects the platform if not specified.
    """
    logger.banner("Deploy")

    # Find project root
    project_root = get_project_root()
    if not project_root:
        project_root = Path.cwd()

    # Load config
    config_path = project_root / "nitro.config.py"
    if config_path.exists():
        config = load_config(config_path)
        build_dir = project_root / config.build_dir
    else:
        build_dir = project_root / "build"

    # Build first if requested
    if build:
        info("Building site for production...")
        from .build import build as build_cmd

        ctx = click.Context(build_cmd)
        try:
            ctx.invoke(
                build_cmd, minify=True, optimize=True, fingerprint=True, quiet=True
            )
        except SystemExit as e:
            if e.code != 0:
                error("Build failed, aborting deployment")
                sys.exit(1)

    # Check build directory exists
    if not build_dir.exists():
        error(f"Build directory not found: {build_dir}")
        info("Run 'nitro build' first")
        sys.exit(1)

    # Auto-detect platform
    if platform == "auto":
        platform = _detect_platform(project_root)
        if platform:
            info(f"Detected platform: {platform}")
        else:
            error("Could not auto-detect deployment platform")
            info("Specify a platform with --platform [netlify|vercel|cloudflare]")
            sys.exit(1)

    # Deploy to selected platform
    if platform == "netlify":
        _deploy_netlify(build_dir, prod, verbose)
    elif platform == "vercel":
        _deploy_vercel(build_dir, prod, verbose)
    elif platform == "cloudflare":
        _deploy_cloudflare(build_dir, prod, verbose)


def _detect_platform(project_root: Path) -> str:
    """Auto-detect the deployment platform.

    Args:
        project_root: Project root directory

    Returns:
        Platform name or None
    """
    # Check for platform-specific files
    if (project_root / "netlify.toml").exists():
        return "netlify"
    if (project_root / "vercel.json").exists():
        return "vercel"
    if (project_root / "wrangler.toml").exists():
        return "cloudflare"

    # Check for installed CLIs
    if shutil.which("netlify"):
        return "netlify"
    if shutil.which("vercel"):
        return "vercel"
    if shutil.which("wrangler"):
        return "cloudflare"

    return None


def _deploy_netlify(build_dir: Path, prod: bool, verbose: bool):
    """Deploy to Netlify.

    Args:
        build_dir: Build directory
        prod: Production deployment
        verbose: Verbose output
    """
    # Check for Netlify CLI
    if not shutil.which("netlify"):
        error("Netlify CLI not found")
        info("Install with: npm install -g netlify-cli")
        info("Then run: netlify login")
        sys.exit(1)

    logger.section("Deploying to Netlify")

    cmd = ["netlify", "deploy", "--dir", str(build_dir)]
    if prod:
        cmd.append("--prod")
        info("Deploying to production...")
    else:
        info("Creating preview deployment...")
        info("Use --prod for production deployment")

    if verbose:
        info(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=not verbose, text=True)

        if result.returncode == 0:
            success("Deployment successful!")
            if not verbose and result.stdout:
                # Extract URL from output
                for line in result.stdout.split("\n"):
                    if "Website URL:" in line or "Website Draft URL:" in line:
                        logger.print(line.strip())
        else:
            error("Deployment failed")
            if result.stderr:
                logger.print(result.stderr)
            sys.exit(1)

    except Exception as e:
        error(f"Deployment error: {e}")
        sys.exit(1)


def _deploy_vercel(build_dir: Path, prod: bool, verbose: bool):
    """Deploy to Vercel.

    Args:
        build_dir: Build directory
        prod: Production deployment
        verbose: Verbose output
    """
    # Check for Vercel CLI
    if not shutil.which("vercel"):
        error("Vercel CLI not found")
        info("Install with: npm install -g vercel")
        info("Then run: vercel login")
        sys.exit(1)

    logger.section("Deploying to Vercel")

    # Vercel deploys the current directory, so we need to deploy from build_dir
    cmd = ["vercel", str(build_dir)]
    if prod:
        cmd.append("--prod")
        info("Deploying to production...")
    else:
        info("Creating preview deployment...")
        info("Use --prod for production deployment")

    # Add yes flag to skip prompts
    cmd.extend(["--yes"])

    if verbose:
        info(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=not verbose, text=True)

        if result.returncode == 0:
            success("Deployment successful!")
            if not verbose and result.stdout:
                # The URL is usually the last non-empty line
                lines = [ln.strip() for ln in result.stdout.split("\n") if ln.strip()]
                if lines:
                    info(f"URL: {lines[-1]}")
        else:
            error("Deployment failed")
            if result.stderr:
                logger.print(result.stderr)
            sys.exit(1)

    except Exception as e:
        error(f"Deployment error: {e}")
        sys.exit(1)


def _deploy_cloudflare(build_dir: Path, prod: bool, verbose: bool):
    """Deploy to Cloudflare Pages.

    Args:
        build_dir: Build directory
        prod: Production deployment
        verbose: Verbose output
    """
    # Check for Wrangler CLI
    if not shutil.which("wrangler"):
        error("Wrangler CLI not found")
        info("Install with: npm install -g wrangler")
        info("Then run: wrangler login")
        sys.exit(1)

    logger.section("Deploying to Cloudflare Pages")

    # Get project name from config or directory
    project_root = get_project_root() or Path.cwd()
    project_name = project_root.name.lower().replace("_", "-").replace(" ", "-")

    cmd = [
        "wrangler",
        "pages",
        "deploy",
        str(build_dir),
        "--project-name",
        project_name,
    ]

    if prod:
        cmd.extend(["--branch", "main"])
        info("Deploying to production...")
    else:
        info("Creating preview deployment...")
        info("Use --prod for production deployment")

    if verbose:
        info(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=not verbose, text=True)

        if result.returncode == 0:
            success("Deployment successful!")
            if not verbose and result.stdout:
                for line in result.stdout.split("\n"):
                    if ".pages.dev" in line:
                        logger.print(line.strip())
        else:
            error("Deployment failed")
            if result.stderr:
                logger.print(result.stderr)
            # Cloudflare might prompt to create the project
            if "does not exist" in (result.stderr or ""):
                info("You may need to create the project first:")
                info(f"  wrangler pages project create {project_name}")
            sys.exit(1)

    except Exception as e:
        error(f"Deployment error: {e}")
        sys.exit(1)
