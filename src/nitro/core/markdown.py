"""Markdown processing with frontmatter support."""

from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MarkdownDocument:
    """Represents a parsed Markdown document with frontmatter."""

    content: str
    raw_content: str
    frontmatter: Dict[str, Any] = field(default_factory=dict)
    path: Optional[Path] = None

    @property
    def title(self) -> Optional[str]:
        """Get the title from frontmatter."""
        return self.frontmatter.get("title")

    @property
    def date(self) -> Optional[datetime]:
        """Get the date from frontmatter."""
        date_val = self.frontmatter.get("date")
        if isinstance(date_val, datetime):
            return date_val
        if isinstance(date_val, str):
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%B %d, %Y"]:
                try:
                    return datetime.strptime(date_val, fmt)
                except ValueError:
                    continue
        return None

    @property
    def slug(self) -> Optional[str]:
        """Get or generate the slug."""
        if "slug" in self.frontmatter:
            return self.frontmatter["slug"]
        if self.path:
            return self.path.stem
        return None

    @property
    def tags(self) -> List[str]:
        """Get tags from frontmatter."""
        tags = self.frontmatter.get("tags", [])
        if isinstance(tags, str):
            return [t.strip() for t in tags.split(",")]
        return tags if isinstance(tags, list) else []

    @property
    def draft(self) -> bool:
        """Check if this is a draft."""
        return self.frontmatter.get("draft", False)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a frontmatter value."""
        return self.frontmatter.get(key, default)


class MarkdownProcessor:
    """Processes Markdown files with frontmatter."""

    def __init__(self, extensions: Optional[List[str]] = None):
        """Initialize the processor.

        Args:
            extensions: List of markdown extensions to enable
        """
        self.extensions = extensions or [
            "fenced_code",
            "tables",
            "toc",
            "attr_list",
            "def_list",
            "footnotes",
            "meta",
        ]
        self._markdown = None
        self._frontmatter = None

    def _ensure_dependencies(self) -> bool:
        """Check and import required dependencies.

        Returns:
            True if dependencies are available
        """
        try:
            import markdown
            import frontmatter as fm

            self._markdown = markdown
            self._frontmatter = fm
            return True
        except ImportError:
            return False

    def parse(
        self, content: str, path: Optional[Path] = None
    ) -> Optional[MarkdownDocument]:
        """Parse a Markdown string with frontmatter.

        Args:
            content: Markdown content with optional frontmatter
            path: Optional source path

        Returns:
            MarkdownDocument or None if dependencies not available
        """
        if not self._ensure_dependencies():
            return None

        # Parse frontmatter
        post = self._frontmatter.loads(content)

        # Convert markdown to HTML
        md = self._markdown.Markdown(extensions=self.extensions)
        html_content = md.convert(post.content)

        return MarkdownDocument(
            content=html_content,
            raw_content=post.content,
            frontmatter=post.metadata,
            path=path,
        )

    def parse_file(self, path: Path) -> Optional[MarkdownDocument]:
        """Parse a Markdown file with frontmatter.

        Args:
            path: Path to markdown file

        Returns:
            MarkdownDocument or None if dependencies not available
        """
        if not path.exists():
            return None

        content = path.read_text(encoding="utf-8")
        return self.parse(content, path)

    def find_content_files(
        self,
        content_dir: Path,
        pattern: str = "**/*.md",
        include_drafts: bool = False,
    ) -> List[MarkdownDocument]:
        """Find and parse all markdown files in a directory.

        Args:
            content_dir: Directory to search
            pattern: Glob pattern for finding files
            include_drafts: Include draft documents

        Returns:
            List of parsed MarkdownDocument objects
        """
        if not content_dir.exists():
            return []

        documents = []
        for md_file in content_dir.glob(pattern):
            doc = self.parse_file(md_file)
            if doc:
                # Skip drafts unless requested
                if not include_drafts and doc.draft:
                    continue
                documents.append(doc)

        # Sort by date (newest first) if dates are available
        documents.sort(
            key=lambda d: d.date or datetime.min,
            reverse=True,
        )

        return documents


# Global processor instance
_processor = MarkdownProcessor()


def parse_markdown(
    content: str, path: Optional[Path] = None
) -> Optional[MarkdownDocument]:
    """Parse a Markdown string with frontmatter.

    Args:
        content: Markdown content
        path: Optional source path

    Returns:
        MarkdownDocument or None
    """
    return _processor.parse(content, path)


def parse_markdown_file(path: Path) -> Optional[MarkdownDocument]:
    """Parse a Markdown file with frontmatter.

    Args:
        path: Path to markdown file

    Returns:
        MarkdownDocument or None
    """
    return _processor.parse_file(path)


def find_markdown_files(
    content_dir: Path,
    pattern: str = "**/*.md",
    include_drafts: bool = False,
) -> List[MarkdownDocument]:
    """Find and parse all markdown files in a directory.

    Args:
        content_dir: Directory to search
        pattern: Glob pattern
        include_drafts: Include drafts

    Returns:
        List of MarkdownDocument objects
    """
    return _processor.find_content_files(content_dir, pattern, include_drafts)
