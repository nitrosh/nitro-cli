"""Deploy command for one-click deployments."""

import subprocess
import shutil
import sys
from pathlib import Path

import click

from ..core.config import load_config
from ..core.page import get_project_root
from ..utils import info, success, error, header, spinner, console


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
    """Deploy the site to a hosting platform."""
    project_root = get_project_root()
    if not project_root:
        project_root = Path.cwd()

    config_path = project_root / "nitro.config.py"
    if config_path.exists():
        config = load_config(config_path)
        build_dir = project_root / config.build_dir
    else:
        build_dir = project_root / "build"

    if build:
        from .build import build as build_cmd

        ctx = click.Context(build_cmd)
        try:
            ctx.invoke(
                build_cmd, minify=True, optimize=True, fingerprint=True, quiet=True
            )
        except SystemExit as e:
            if e.code not in (0, None):
                error("Build failed, aborting deployment")
                sys.exit(1)

    if not build_dir.exists():
        error(f"Build directory not found: {build_dir}")
        info("Run 'nitro build' first")
        sys.exit(1)

    if platform == "auto":
        platform = _detect_platform(project_root)
        if not platform:
            error("Could not auto-detect deployment platform")
            info("Specify a platform with --platform [netlify|vercel|cloudflare]")
            sys.exit(1)

    header(f"Deploying to {platform.capitalize()}...")

    if platform == "netlify":
        _deploy_netlify(build_dir, prod, verbose)
    elif platform == "vercel":
        _deploy_vercel(build_dir, prod, verbose)
    elif platform == "cloudflare":
        _deploy_cloudflare(build_dir, prod, verbose)


def _detect_platform(project_root: Path) -> str:
    """Auto-detect the deployment platform."""
    if (project_root / "netlify.toml").exists():
        return "netlify"
    if (project_root / "vercel.json").exists():
        return "vercel"
    if (project_root / "wrangler.toml").exists():
        return "cloudflare"

    if shutil.which("netlify"):
        return "netlify"
    if shutil.which("vercel"):
        return "vercel"
    if shutil.which("wrangler"):
        return "cloudflare"

    return None


def _deploy_netlify(build_dir: Path, prod: bool, verbose: bool):
    """Deploy to Netlify."""
    if not shutil.which("netlify"):
        error("Netlify CLI not found")
        info("Install with: npm install -g netlify-cli")
        info("Then run: netlify login")
        sys.exit(1)

    cmd = ["netlify", "deploy", "--dir", str(build_dir)]
    if prod:
        cmd.append("--prod")

    if verbose:
        info(f"Running: {' '.join(cmd)}")

    try:
        with spinner("Uploading to Netlify...") as update:
            result = subprocess.run(
                cmd, capture_output=not verbose, text=True, timeout=300
            )

        if result.returncode == 0:
            success("Deployment successful!")
            if not verbose and result.stdout:
                for line in result.stdout.split("\n"):
                    if "Website URL:" in line or "Website Draft URL:" in line:
                        console.print(line.strip())
        else:
            error("Deployment failed")
            if result.stderr:
                console.print(result.stderr)
            sys.exit(1)

    except subprocess.TimeoutExpired:
        error("Deployment timed out after 5 minutes")
        sys.exit(1)
    except Exception as e:
        error(f"Deployment error: {e}")
        sys.exit(1)


def _deploy_vercel(build_dir: Path, prod: bool, verbose: bool):
    """Deploy to Vercel."""
    if not shutil.which("vercel"):
        error("Vercel CLI not found")
        info("Install with: npm install -g vercel")
        info("Then run: vercel login")
        sys.exit(1)

    cmd = ["vercel", str(build_dir)]
    if prod:
        cmd.append("--prod")
    cmd.extend(["--yes"])

    if verbose:
        info(f"Running: {' '.join(cmd)}")

    try:
        with spinner("Uploading to Vercel...") as update:
            result = subprocess.run(
                cmd, capture_output=not verbose, text=True, timeout=300
            )

        if result.returncode == 0:
            success("Deployment successful!")
            if not verbose and result.stdout:
                lines = [ln.strip() for ln in result.stdout.split("\n") if ln.strip()]
                if lines:
                    info(f"URL: {lines[-1]}")
        else:
            error("Deployment failed")
            if result.stderr:
                console.print(result.stderr)
            sys.exit(1)

    except subprocess.TimeoutExpired:
        error("Deployment timed out after 5 minutes")
        sys.exit(1)
    except Exception as e:
        error(f"Deployment error: {e}")
        sys.exit(1)


def _deploy_cloudflare(build_dir: Path, prod: bool, verbose: bool):
    """Deploy to Cloudflare Pages."""
    if not shutil.which("wrangler"):
        error("Wrangler CLI not found")
        info("Install with: npm install -g wrangler")
        info("Then run: wrangler login")
        sys.exit(1)

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

    if verbose:
        info(f"Running: {' '.join(cmd)}")

    try:
        with spinner("Uploading to Cloudflare...") as update:
            result = subprocess.run(
                cmd, capture_output=not verbose, text=True, timeout=300
            )

        if result.returncode == 0:
            success("Deployment successful!")
            if not verbose and result.stdout:
                for line in result.stdout.split("\n"):
                    if ".pages.dev" in line:
                        console.print(line.strip())
        else:
            error("Deployment failed")
            if result.stderr:
                console.print(result.stderr)
            if "does not exist" in (result.stderr or ""):
                info("You may need to create the project first:")
                info(f"  wrangler pages project create {project_name}")
            sys.exit(1)

    except subprocess.TimeoutExpired:
        error("Deployment timed out after 5 minutes")
        sys.exit(1)
    except Exception as e:
        error(f"Deployment error: {e}")
        sys.exit(1)
