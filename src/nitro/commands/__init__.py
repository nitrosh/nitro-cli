"""Command modules for Nitro CLI."""

from click import Command

from .new import new
from .serve import serve
from .build import build
from .test import test
from .docs import docs

# Type annotations for IDE/type checkers
new: Command
serve: Command
build: Command
test: Command
docs: Command

__all__ = ["new", "serve", "build", "test", "docs"]
