"""Content collections with schema validation.

Similar to Astro's content collections - define typed collections of content
(blog posts, docs, etc.) with frontmatter validation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
import re

from ..utils import error, warning, info


# Schema field types
class SchemaField:
    """Base class for schema field definitions."""

    def __init__(
        self,
        required: bool = True,
        default: Any = None,
        description: str = "",
    ):
        self.required = required
        self.default = default
        self.description = description

    def validate(self, value: Any, field_name: str) -> tuple[bool, Any, Optional[str]]:
        """Validate a value against this field.

        Args:
            value: The value to validate
            field_name: Name of the field (for error messages)

        Returns:
            Tuple of (is_valid, coerced_value, error_message)
        """
        raise NotImplementedError


class StringField(SchemaField):
    """String field with optional constraints."""

    def __init__(
        self,
        required: bool = True,
        default: str = "",
        min_length: int = 0,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        choices: Optional[List[str]] = None,
        description: str = "",
    ):
        super().__init__(required, default, description)
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = re.compile(pattern) if pattern else None
        self.choices = choices

    def validate(self, value: Any, field_name: str) -> tuple[bool, Any, Optional[str]]:
        if value is None:
            if self.required:
                return False, None, f"'{field_name}' is required"
            return True, self.default, None

        if not isinstance(value, str):
            value = str(value)

        if len(value) < self.min_length:
            return (
                False,
                None,
                f"'{field_name}' must be at least {self.min_length} characters",
            )

        if self.max_length and len(value) > self.max_length:
            return (
                False,
                None,
                f"'{field_name}' must be at most {self.max_length} characters",
            )

        if self.pattern and not self.pattern.match(value):
            return False, None, f"'{field_name}' does not match required pattern"

        if self.choices and value not in self.choices:
            return (
                False,
                None,
                f"'{field_name}' must be one of: {', '.join(self.choices)}",
            )

        return True, value, None


class NumberField(SchemaField):
    """Numeric field (int or float)."""

    def __init__(
        self,
        required: bool = True,
        default: Union[int, float] = 0,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        integer_only: bool = False,
        description: str = "",
    ):
        super().__init__(required, default, description)
        self.min_value = min_value
        self.max_value = max_value
        self.integer_only = integer_only

    def validate(self, value: Any, field_name: str) -> tuple[bool, Any, Optional[str]]:
        if value is None:
            if self.required:
                return False, None, f"'{field_name}' is required"
            return True, self.default, None

        try:
            if self.integer_only:
                value = int(value)
            else:
                value = float(value)
        except (ValueError, TypeError):
            return False, None, f"'{field_name}' must be a number"

        if self.min_value is not None and value < self.min_value:
            return False, None, f"'{field_name}' must be at least {self.min_value}"

        if self.max_value is not None and value > self.max_value:
            return False, None, f"'{field_name}' must be at most {self.max_value}"

        return True, value, None


class BooleanField(SchemaField):
    """Boolean field."""

    def __init__(
        self,
        required: bool = True,
        default: bool = False,
        description: str = "",
    ):
        super().__init__(required, default, description)

    def validate(self, value: Any, field_name: str) -> tuple[bool, Any, Optional[str]]:
        if value is None:
            if self.required:
                return False, None, f"'{field_name}' is required"
            return True, self.default, None

        if isinstance(value, bool):
            return True, value, None

        if isinstance(value, str):
            if value.lower() in ("true", "yes", "1", "on"):
                return True, True, None
            if value.lower() in ("false", "no", "0", "off"):
                return True, False, None

        return False, None, f"'{field_name}' must be a boolean"


class DateField(SchemaField):
    """Date/datetime field."""

    def __init__(
        self,
        required: bool = True,
        default: Optional[datetime] = None,
        description: str = "",
    ):
        super().__init__(required, default, description)

    def validate(self, value: Any, field_name: str) -> tuple[bool, Any, Optional[str]]:
        if value is None:
            if self.required:
                return False, None, f"'{field_name}' is required"
            return True, self.default, None

        if isinstance(value, datetime):
            return True, value, None

        if isinstance(value, str):
            # Try common date formats
            formats = [
                "%Y-%m-%d",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d %H:%M:%S",
                "%d/%m/%Y",
                "%m/%d/%Y",
            ]
            for fmt in formats:
                try:
                    return True, datetime.strptime(value, fmt), None
                except ValueError:
                    continue

        return False, None, f"'{field_name}' must be a valid date"


class ListField(SchemaField):
    """List/array field with optional item type."""

    def __init__(
        self,
        item_type: Optional[SchemaField] = None,
        required: bool = True,
        default: Optional[List] = None,
        min_items: int = 0,
        max_items: Optional[int] = None,
        description: str = "",
    ):
        super().__init__(required, default or [], description)
        self.item_type = item_type
        self.min_items = min_items
        self.max_items = max_items

    def validate(self, value: Any, field_name: str) -> tuple[bool, Any, Optional[str]]:
        if value is None:
            if self.required:
                return False, None, f"'{field_name}' is required"
            return True, self.default, None

        if not isinstance(value, (list, tuple)):
            # Try to convert single value to list
            value = [value]

        if len(value) < self.min_items:
            return (
                False,
                None,
                f"'{field_name}' must have at least {self.min_items} items",
            )

        if self.max_items and len(value) > self.max_items:
            return (
                False,
                None,
                f"'{field_name}' must have at most {self.max_items} items",
            )

        # Validate each item if item_type is specified
        if self.item_type:
            validated_items = []
            for i, item in enumerate(value):
                is_valid, coerced, err = self.item_type.validate(
                    item, f"{field_name}[{i}]"
                )
                if not is_valid:
                    return False, None, err
                validated_items.append(coerced)
            return True, validated_items, None

        return True, list(value), None


class EnumField(SchemaField):
    """Enumeration field with predefined choices."""

    def __init__(
        self,
        choices: List[str],
        required: bool = True,
        default: Optional[str] = None,
        description: str = "",
    ):
        super().__init__(required, default, description)
        self.choices = choices

    def validate(self, value: Any, field_name: str) -> tuple[bool, Any, Optional[str]]:
        if value is None:
            if self.required:
                return False, None, f"'{field_name}' is required"
            return True, self.default, None

        if value not in self.choices:
            return (
                False,
                None,
                f"'{field_name}' must be one of: {', '.join(self.choices)}",
            )

        return True, value, None


class SlugField(StringField):
    """URL-safe slug field."""

    def __init__(
        self,
        required: bool = True,
        default: str = "",
        auto_generate: bool = True,
        description: str = "",
    ):
        # Slug pattern: lowercase letters, numbers, and hyphens
        super().__init__(
            required=required,
            default=default,
            pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
            description=description,
        )
        self.auto_generate = auto_generate

    def validate(self, value: Any, field_name: str) -> tuple[bool, Any, Optional[str]]:
        if value is None and self.auto_generate:
            return True, None, None  # Will be auto-generated from filename

        return super().validate(value, field_name)


@dataclass
class CollectionSchema:
    """Schema definition for a content collection."""

    fields: Dict[str, SchemaField] = field(default_factory=dict)
    strict: bool = False  # If True, reject unknown fields

    def validate(self, data: Dict[str, Any]) -> tuple[bool, Dict[str, Any], List[str]]:
        """Validate data against the schema.

        Args:
            data: Dictionary of frontmatter data

        Returns:
            Tuple of (is_valid, validated_data, errors)
        """
        errors = []
        validated = {}

        # Validate defined fields
        for field_name, field_schema in self.fields.items():
            value = data.get(field_name)
            is_valid, coerced, err = field_schema.validate(value, field_name)

            if not is_valid:
                errors.append(err)
            else:
                validated[field_name] = coerced

        # Check for unknown fields in strict mode
        if self.strict:
            for key in data:
                if key not in self.fields:
                    errors.append(f"Unknown field '{key}' (strict mode enabled)")

        # Pass through unknown fields in non-strict mode
        if not self.strict:
            for key, value in data.items():
                if key not in self.fields:
                    validated[key] = value

        return len(errors) == 0, validated, errors


@dataclass
class CollectionEntry:
    """A single entry in a content collection."""

    id: str  # Unique identifier (usually filename without extension)
    slug: str  # URL slug
    data: Dict[str, Any]  # Validated frontmatter
    content: str  # HTML content
    raw_content: str  # Original markdown
    path: Path  # Source file path
    collection: str  # Collection name


class ContentCollection:
    """A typed content collection with schema validation."""

    def __init__(
        self,
        name: str,
        schema: CollectionSchema,
        content_dir: Path,
    ):
        """Initialize a content collection.

        Args:
            name: Collection name
            schema: Schema for validation
            content_dir: Directory containing collection content
        """
        self.name = name
        self.schema = schema
        self.content_dir = content_dir
        self._entries: List[CollectionEntry] = []
        self._loaded = False

    def load(self, markdown_processor=None) -> List[CollectionEntry]:
        """Load and validate all entries in the collection.

        Args:
            markdown_processor: Optional MarkdownProcessor instance

        Returns:
            List of validated collection entries
        """
        if self._loaded:
            return self._entries

        from .markdown import MarkdownProcessor

        processor = markdown_processor or MarkdownProcessor()
        self._entries = []
        validation_errors = []

        if not self.content_dir.exists():
            warning(f"Collection directory not found: {self.content_dir}")
            return self._entries

        # Find all markdown files
        md_files = list(self.content_dir.glob("**/*.md"))

        for md_file in md_files:
            try:
                doc = processor.process_file(md_file)

                # Get ID from filename
                entry_id = md_file.stem

                # Validate frontmatter
                is_valid, validated_data, errors = self.schema.validate(doc.frontmatter)

                if not is_valid:
                    for err in errors:
                        validation_errors.append(f"{md_file.name}: {err}")
                    continue

                # Generate slug if not provided
                slug = validated_data.get("slug") or entry_id

                entry = CollectionEntry(
                    id=entry_id,
                    slug=slug,
                    data=validated_data,
                    content=doc.content,
                    raw_content=doc.raw_content,
                    path=md_file,
                    collection=self.name,
                )
                self._entries.append(entry)

            except Exception as e:
                validation_errors.append(f"{md_file.name}: {e}")

        if validation_errors:
            error(f"Validation errors in '{self.name}' collection:")
            for err in validation_errors:
                warning(f"  - {err}")

        self._loaded = True
        return self._entries

    @property
    def entries(self) -> List[CollectionEntry]:
        """Get all entries (loads if needed)."""
        if not self._loaded:
            self.load()
        return self._entries

    def get(self, id_or_slug: str) -> Optional[CollectionEntry]:
        """Get an entry by ID or slug.

        Args:
            id_or_slug: Entry ID or slug

        Returns:
            CollectionEntry or None
        """
        for entry in self.entries:
            if entry.id == id_or_slug or entry.slug == id_or_slug:
                return entry
        return None

    def filter(
        self,
        predicate: Callable[[CollectionEntry], bool],
    ) -> List[CollectionEntry]:
        """Filter entries by a predicate function.

        Args:
            predicate: Function that returns True for entries to include

        Returns:
            Filtered list of entries
        """
        return [e for e in self.entries if predicate(e)]

    def sort(
        self,
        key: Union[str, Callable[[CollectionEntry], Any]],
        reverse: bool = False,
    ) -> List[CollectionEntry]:
        """Sort entries by a key.

        Args:
            key: Field name or function to extract sort key
            reverse: Sort in descending order

        Returns:
            Sorted list of entries
        """
        if isinstance(key, str):
            field_name = key

            def get_field(e):
                return e.data.get(field_name, "")

            key = get_field

        return sorted(self.entries, key=key, reverse=reverse)

    def where(self, **conditions) -> List[CollectionEntry]:
        """Filter entries by field values.

        Args:
            **conditions: Field name to value mappings

        Returns:
            Filtered list of entries
        """

        def matches(entry: CollectionEntry) -> bool:
            for field_name, expected in conditions.items():
                actual = entry.data.get(field_name)
                if callable(expected):
                    if not expected(actual):
                        return False
                elif actual != expected:
                    return False
            return True

        return self.filter(matches)

    def group_by(self, key: str) -> Dict[Any, List[CollectionEntry]]:
        """Group entries by a field value.

        Args:
            key: Field name to group by

        Returns:
            Dictionary mapping values to entries
        """
        groups: Dict[Any, List[CollectionEntry]] = {}
        for entry in self.entries:
            value = entry.data.get(key)
            if value not in groups:
                groups[value] = []
            groups[value].append(entry)
        return groups

    def __len__(self) -> int:
        return len(self.entries)

    def __iter__(self):
        return iter(self.entries)


class CollectionRegistry:
    """Registry for all content collections in a project."""

    def __init__(self, project_root: Path):
        """Initialize the collection registry.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root
        self.content_dir = project_root / "content"
        self._collections: Dict[str, ContentCollection] = {}

    def define(
        self,
        name: str,
        schema: Optional[CollectionSchema] = None,
        directory: Optional[str] = None,
    ) -> ContentCollection:
        """Define a new collection.

        Args:
            name: Collection name
            schema: Optional schema for validation
            directory: Optional subdirectory name (defaults to collection name)

        Returns:
            The created ContentCollection
        """
        if schema is None:
            schema = CollectionSchema()

        content_dir = self.content_dir / (directory or name)
        collection = ContentCollection(name, schema, content_dir)
        self._collections[name] = collection
        return collection

    def get(self, name: str) -> Optional[ContentCollection]:
        """Get a collection by name.

        Args:
            name: Collection name

        Returns:
            ContentCollection or None
        """
        return self._collections.get(name)

    def all(self) -> Dict[str, ContentCollection]:
        """Get all registered collections.

        Returns:
            Dictionary of collection name to ContentCollection
        """
        return self._collections

    def load_from_config(self, config_path: Path) -> None:
        """Load collection definitions from a config file.

        The config file should be a Python file that defines collections:

        ```python
        # content.config.py
        from nitro.core.collections import *

        collections = {
            "blog": CollectionSchema(
                fields={
                    "title": StringField(required=True),
                    "date": DateField(required=True),
                    "author": StringField(required=False, default="Anonymous"),
                    "tags": ListField(item_type=StringField()),
                    "draft": BooleanField(default=False),
                }
            ),
            "docs": CollectionSchema(
                fields={
                    "title": StringField(required=True),
                    "order": NumberField(integer_only=True, default=0),
                    "category": EnumField(choices=["guide", "api", "tutorial"]),
                }
            ),
        }
        ```

        Args:
            config_path: Path to the config file
        """
        if not config_path.exists():
            return

        import importlib.util

        spec = importlib.util.spec_from_file_location("content_config", config_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "collections"):
                for name, schema in module.collections.items():
                    self.define(name, schema)

    def auto_discover(self) -> None:
        """Auto-discover collections from content directory structure.

        Each subdirectory in content/ becomes a collection with a default schema.
        """
        if not self.content_dir.exists():
            return

        for item in self.content_dir.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                if item.name not in self._collections:
                    # Create with default schema
                    self.define(item.name)
                    info(f"Auto-discovered collection: {item.name}")


# Convenience functions for creating common schemas
def blog_schema(**overrides) -> CollectionSchema:
    """Create a common blog post schema.

    Args:
        **overrides: Field overrides

    Returns:
        CollectionSchema for blog posts
    """
    fields = {
        "title": StringField(required=True, description="Post title"),
        "date": DateField(required=True, description="Publication date"),
        "author": StringField(required=False, default="", description="Author name"),
        "description": StringField(
            required=False, default="", max_length=160, description="Meta description"
        ),
        "tags": ListField(
            item_type=StringField(), required=False, description="Post tags"
        ),
        "draft": BooleanField(
            required=False, default=False, description="Draft status"
        ),
        "featured": BooleanField(
            required=False, default=False, description="Featured post"
        ),
        "image": StringField(
            required=False, default="", description="Featured image URL"
        ),
    }
    fields.update(overrides)
    return CollectionSchema(fields=fields)


def docs_schema(**overrides) -> CollectionSchema:
    """Create a common documentation schema.

    Args:
        **overrides: Field overrides

    Returns:
        CollectionSchema for documentation
    """
    fields = {
        "title": StringField(required=True, description="Page title"),
        "description": StringField(
            required=False, default="", description="Page description"
        ),
        "order": NumberField(
            required=False, default=0, integer_only=True, description="Sort order"
        ),
        "category": StringField(required=False, default="", description="Category"),
        "sidebar": BooleanField(
            required=False, default=True, description="Show in sidebar"
        ),
    }
    fields.update(overrides)
    return CollectionSchema(fields=fields)
