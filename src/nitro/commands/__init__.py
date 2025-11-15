"""Command modules for Nitro CLI."""

from click import Command

from .scaffold import scaffold
from .generate import generate
from .serve import serve
from .build import build
from .test import test
from .docs import docs

# Type annotations for IDE/type checkers
scaffold: Command
generate: Command
serve: Command
build: Command
test: Command
docs: Command

__all__ = ["scaffold", "generate", "serve", "build", "test", "docs"]
