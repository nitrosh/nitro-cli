"""Command modules for Nitro CLI."""

from click import Command

from .new import new
from .serve import serve
from .dev import dev
from .build import build
from .preview import preview
from .clean import clean
from .info import info
from .deploy import deploy
from .test import test
from .docs import docs

# Type annotations for IDE/type checkers
new: Command
serve: Command
dev: Command
build: Command
preview: Command
clean: Command
info: Command
deploy: Command
test: Command
docs: Command

__all__ = [
    "new",
    "serve",
    "dev",
    "build",
    "preview",
    "clean",
    "info",
    "deploy",
    "test",
    "docs",
]
