# NitroDataStore

**Flexible, schema-agnostic data management for your Nitro projects.**

NitroDataStore is a powerful Python class for working with JSON and YAML data files. It provides multiple access patterns, advanced querying, and data manipulation tools that work with any user-defined data structure.

## Quick Start

```python
from nitro import NitroDataStore

# Create from a dictionary
data = NitroDataStore({
    'site': {
        'name': 'My Awesome Site',
        'url': 'https://example.com'
    }
})

# Multiple ways to access the same value
data.site.name                    # Dot notation
data['site']['name']              # Dictionary access
data.get('site.name')             # Path-based access
```

## Table of Contents

1. [Installation](#installation)
2. [Creating a DataStore](#creating-a-datastore)
3. [Access Patterns](#access-patterns)
4. [Basic Operations](#basic-operations)
5. [File Operations](#file-operations)
6. [Path Introspection](#path-introspection)
7. [Deep Search](#deep-search)
8. [Bulk Operations](#bulk-operations)
9. [Query Builder](#query-builder)
10. [Transformations](#transformations)
11. [Data Introspection](#data-introspection)
12. [Comparison](#comparison)
13. [Integration with Nitro Pages](#integration-with-nitro-pages)
14. [Best Practices](#best-practices)
15. [API Reference](#api-reference)

## Installation

NitroDataStore is included with Nitro CLI:

```bash
pip install nitro-cli
```

Or in development mode:

```bash
pip install -e .
```

## Creating a DataStore

### From a Dictionary

```python
data = NitroDataStore({
    'title': 'Welcome',
    'settings': {
        'theme': 'dark',
        'language': 'en'
    }
})
```

### From a JSON File

```python
data = NitroDataStore.from_file('data/config.json')
```

### From a Directory (Auto-merge)

Load and merge all JSON files from a directory. Files are merged alphabetically, with later files overriding earlier ones:

```python
data = NitroDataStore.from_directory('data/')
```

**Example:**

**data/site.json:**
```json
{
  "site": {
    "name": "My Site",
    "url": "https://example.com"
  }
}
```

**data/theme.json:**
```json
{
  "site": {
    "name": "Updated Site Name"
  },
  "theme": {
    "colors": {
      "primary": "#007bff"
    }
  }
}
```

**Result:**
```python
data.site.name  # "Updated Site Name" (overridden by theme.json)
data.site.url   # "https://example.com" (preserved from site.json)
data.theme.colors.primary  # "#007bff" (added by theme.json)
```

## Access Patterns

NitroDataStore supports three access patterns - use whichever feels most natural:

### 1. Dot Notation (Recommended)

```python
data = NitroDataStore({
    'user': {
        'name': 'Alice',
        'email': 'alice@example.com'
    }
})

# Read
print(data.user.name)  # "Alice"

# Write
data.user.name = 'Bob'
```

### 2. Dictionary Access

```python
# Read
print(data['user']['name'])  # "Bob"

# Write
data['user']['email'] = 'bob@example.com'

# Check existence
if 'user' in data:
    print("User data exists")

# Delete
del data['user']['email']
```

### 3. Path-based Access

Best for dynamic paths and defaults:

```python
# Get with defaults
name = data.get('user.name', 'Anonymous')
theme = data.get('user.settings.theme', 'light')

# Set nested values (creates intermediate dicts)
data.set('config.cache.ttl', 3600)

# Delete nested values
deleted = data.delete('config.cache.ttl')

# Check existence
if data.has('user.settings.notifications'):
    print("Notifications setting exists")
```

## Basic Operations

### Setting Values

```python
data = NitroDataStore()

# Simple values
data.set('title', 'My Page')
data.set('count', 42)

# Nested values (auto-creates intermediate dicts)
data.set('config.theme.colors.primary', '#007bff')

# Lists and complex structures
data.set('tags', ['python', 'web', 'static-site'])
```

### Getting Values

```python
# With defaults
title = data.get('title', 'Untitled')
color = data.get('config.theme.colors.primary', '#000000')

# Check before accessing
if data.has('featured.post'):
    featured = data.get('featured.post')
```

### Merging Data

```python
base = NitroDataStore({'site': {'name': 'Original', 'url': 'example.com'}})
updates = NitroDataStore({'site': {'name': 'New Name'}, 'theme': 'dark'})

base.merge(updates)

# Result: site.name updated, site.url preserved, theme added
```

### Iteration

```python
# Iterate over top-level keys
for key in data.keys():
    print(key)

# Iterate over values
for value in data.values():
    print(value)

# Iterate over items
for key, value in data.items():
    print(f"{key}: {value}")
```

## File Operations

### Loading Data

```python
# From JSON file
config = NitroDataStore.from_file('config.json')

# From directory with custom pattern
data = NitroDataStore.from_directory('data/', pattern='*.config.json')

# Using load_data() helper
from nitro import load_data

data = load_data('data/site.json')  # Returns NitroDataStore
raw = load_data('data/site.json', wrap=False)  # Returns plain dict
```

### Saving Data

```python
data = NitroDataStore({'site': {'name': 'My Site'}})

# Save to JSON file (creates parent directories if needed)
data.save('output/config.json')

# Custom indentation
data.save('output/config.json', indent=4)
```

## Path Introspection

Discover and work with paths without knowing the schema in advance.

### list_paths()

List all paths in your data structure:

```python
data = NitroDataStore({
    'site': {'name': 'Test', 'url': 'example.com'},
    'posts': [{'title': 'A'}, {'title': 'B'}]
})

paths = data.list_paths()
# ['site', 'site.name', 'site.url', 'posts', 'posts.0', 'posts.0.title', 'posts.1', 'posts.1.title']

# Filter by prefix
site_paths = data.list_paths(prefix='site')
# ['site', 'site.name', 'site.url']
```

### find_paths()

Find paths matching glob-like patterns:

```python
# Find all titles
titles = data.find_paths('posts.*.title')
# ['posts.0.title', 'posts.1.title']

# Find all 'url' keys anywhere
urls = data.find_paths('**.url')
```

**Wildcards:**
- `*` - Matches any single path segment
- `**` - Matches any number of path segments

### get_many()

Get multiple values at once:

```python
values = data.get_many(['site.name', 'site.url', 'theme', 'missing'])
# {
#     'site.name': 'Test',
#     'site.url': 'example.com',
#     'theme': None,
#     'missing': None
# }
```

## Deep Search

Find values anywhere in your structure based on criteria.

### find_all_keys()

Find all occurrences of a key name:

```python
data = NitroDataStore({
    'site': {'url': 'site.com'},
    'social': {
        'github': {'url': 'github.com/user'},
        'twitter': {'url': 'twitter.com/user'}
    }
})

urls = data.find_all_keys('url')
# {
#     'site.url': 'site.com',
#     'social.github.url': 'github.com/user',
#     'social.twitter.url': 'twitter.com/user'
# }
```

### find_values()

Find values matching a predicate:

```python
# Find all .jpg images
jpgs = data.find_values(lambda v: isinstance(v, str) and v.endswith('.jpg'))

# Find all numbers greater than 100
big_nums = data.find_values(lambda v: isinstance(v, (int, float)) and v > 100)

# Find all email addresses
emails = data.find_values(lambda v: isinstance(v, str) and '@' in v)
```

## Bulk Operations

Perform operations on multiple values at once.

### update_where()

Update all values matching a condition:

```python
# Upgrade all HTTP URLs to HTTPS
count = data.update_where(
    condition=lambda path, value: isinstance(value, str) and 'http://' in value,
    transform=lambda value: value.replace('http://', 'https://')
)
# Returns: number of values updated
```

### remove_nulls()

Remove all `None` values:

```python
data = NitroDataStore({
    'user': {'name': 'Alice', 'email': None},
    'items': [1, None, 2, None, 3]
})

count = data.remove_nulls()  # Returns: 3

# Result: {'user': {'name': 'Alice'}, 'items': [1, 2, 3]}
```

### remove_empty()

Remove all empty dictionaries and lists:

```python
data = NitroDataStore({
    'config': {},
    'tags': [],
    'nested': {'value': 1, 'empty': {}}
})

count = data.remove_empty()  # Returns: 3

# Result: {'nested': {'value': 1}}
```

## Query Builder

Chainable query interface for filtering and transforming collections.

### Basic Usage

```python
data = NitroDataStore({
    'posts': [
        {'title': 'Python Tips', 'category': 'python', 'views': 150, 'published': True},
        {'title': 'Web Dev', 'category': 'web', 'views': 200, 'published': True},
        {'title': 'Draft', 'category': 'python', 'views': 0, 'published': False}
    ]
})

# Get published posts
published = data.query('posts').where(lambda p: p.get('published')).execute()
```

### Filtering with where()

```python
# Multiple conditions (AND logic)
popular_python = (data.query('posts')
    .where(lambda p: p.get('category') == 'python')
    .where(lambda p: p.get('views') > 100)
    .execute())
```

### Sorting

```python
# Ascending
by_views = data.query('posts').sort(key=lambda p: p.get('views')).execute()

# Descending
popular_first = data.query('posts').sort(key=lambda p: p.get('views'), reverse=True).execute()
```

### Pagination

```python
# First page (10 items)
page1 = data.query('posts').limit(10).execute()

# Second page
page2 = data.query('posts').offset(10).limit(10).execute()
```

### Complex Queries

```python
# Published Python posts, sorted by views, top 5
top_python = (data.query('posts')
    .where(lambda p: p.get('category') == 'python')
    .where(lambda p: p.get('published'))
    .sort(key=lambda p: p.get('views'), reverse=True)
    .limit(5)
    .execute())
```

### Utility Methods

```python
# Count without fetching
count = data.query('posts').where(lambda p: p.get('published')).count()

# Get first result only
first = data.query('posts').sort(key=lambda p: p.get('views'), reverse=True).first()

# Extract single field
titles = data.query('posts').pluck('title')
# ['Python Tips', 'Web Dev', 'Draft']

# Group by field
by_category = data.query('posts').group_by('category')
# {'python': [...], 'web': [...]}
```

## Transformations

Create new datastores with transformed data.

### transform_all()

Transform all values:

```python
data = NitroDataStore({
    'user': {'name': 'alice', 'email': 'alice@example.com'}
})

# Uppercase all strings
upper = data.transform_all(lambda path, value: value.upper() if isinstance(value, str) else value)

# Original unchanged
print(data.user.name)  # 'alice'
print(upper.user.name)  # 'ALICE'
```

### transform_keys()

Transform all keys:

```python
data = NitroDataStore({
    'user-info': {'first-name': 'John', 'last-name': 'Doe'}
})

# Convert kebab-case to snake_case
snake = data.transform_keys(lambda k: k.replace('-', '_'))

# Result: {'user_info': {'first_name': 'John', 'last_name': 'Doe'}}
```

## Data Introspection

Understand the structure of your data.

### describe()

Get structural description:

```python
data = NitroDataStore({
    'site': {'name': 'My Site', 'year': 2024},
    'posts': [{'title': 'A'}, {'title': 'B'}],
    'active': True
})

description = data.describe()
# {
#     'site': {
#         'type': 'dict',
#         'keys': ['name', 'year'],
#         'structure': {...}
#     },
#     'posts': {
#         'type': 'list',
#         'length': 2,
#         'item_types': ['dict']
#     },
#     'active': {'type': 'bool', 'value': True}
# }
```

### stats()

Get statistics:

```python
stats = data.stats()
# {
#     'total_keys': 3,
#     'max_depth': 3,
#     'total_dicts': 3,
#     'total_lists': 1,
#     'total_values': 4
# }
```

## Comparison

Compare datastores and detect differences.

### equals()

Check equality:

```python
data1 = NitroDataStore({'name': 'Alice', 'age': 30})
data2 = NitroDataStore({'name': 'Alice', 'age': 30})
data3 = NitroDataStore({'name': 'Bob', 'age': 25})

data1.equals(data2)  # True
data1.equals(data3)  # False
data1.equals({'name': 'Alice', 'age': 30})  # True (works with dicts)
```

### diff()

Find differences:

```python
old = NitroDataStore({'site': {'name': 'Old', 'url': 'example.com'}, 'theme': 'light'})
new = NitroDataStore({'site': {'name': 'New', 'url': 'example.com'}, 'version': '2.0'})

diff = old.diff(new)

# diff['added']: {'version': '2.0'}
# diff['removed']: {'theme': 'light'}
# diff['changed']: {'site.name': {'old': 'Old', 'new': 'New'}}
```

## Integration with Nitro Pages

### Basic Usage in Pages

**src/data/site.json:**
```json
{
  "site": {
    "name": "My Portfolio",
    "tagline": "Building amazing things",
    "author": "Alice Developer"
  }
}
```

**src/pages/index.py:**
```python
from ydnatl import HTML, Head, Body, H1, Paragraph
from nitro import Page, load_data

def render():
    # Load data (automatically wrapped in NitroDataStore)
    data = load_data('data/site.json')

    # Access with dot notation
    return Page(
        title=data.site.name,
        content=HTML(
            Head(title=data.site.name),
            Body(
                H1(data.site.name),
                Paragraph(data.site.tagline),
                Paragraph(f"By {data.site.author}")
            )
        )
    )
```

### Advanced Page Usage

```python
from nitro import Page, load_data

def render():
    # Load site configuration
    site = load_data('data/site.json')

    # Load blog posts
    posts = load_data('data/posts.json')

    # Query for recent published posts
    recent = (posts.query('posts')
        .where(lambda p: p.get('published'))
        .sort(key=lambda p: p.get('date'), reverse=True)
        .limit(5)
        .execute())

    # Safe access with defaults
    title = site.get('site.title', 'Untitled')
    author = site.get('site.author', 'Anonymous')

    # Build page with data
    return Page(
        title=title,
        content=build_html(title, author, recent),
        meta={'description': site.get('site.tagline', '')}
    )
```

## Best Practices

### 1. Use Dot Notation for Static Keys

```python
# Good - clear and concise
data.site.name

# Less ideal for known static keys
data.get('site.name')
```

### 2. Use Path-based get() for Dynamic Keys

```python
# Good - safe with defaults
key = f"user.{user_id}.name"
name = data.get(key, 'Unknown')

# Risky - may raise AttributeError
name = getattr(data.user, user_id).name
```

### 3. Load Data Once, Reuse

```python
# Load at module level
SITE_DATA = load_data('data/site.json')

def render():
    # Reuse loaded data
    return Page(title=SITE_DATA.site.name, ...)
```

### 4. Merge Configuration Hierarchically

```python
# Base config
config = load_data('data/defaults.json')

# Environment overrides
if env == 'production':
    config.merge(load_data('data/production.json'))
```

### 5. Use has() Before Accessing Optional Data

```python
# Good - safe
if data.has('featured.image'):
    image = data.get('featured.image')

# Risky - may raise error
image = data.featured.image
```

## API Reference

### Construction & Loading

| Method | Description |
|--------|-------------|
| `NitroDataStore(data)` | Create from dictionary |
| `from_file(path)` | Load from JSON/YAML file |
| `from_directory(path, pattern='*.json')` | Load and merge from directory |
| `load_data(path, wrap=True)` | Helper function (in `nitro` module) |

### Basic Operations

| Method | Description | Returns |
|--------|-------------|---------|
| `get(key, default=None)` | Get value by path | `Any` |
| `set(key, value)` | Set value by path | `None` |
| `delete(key)` | Delete value by path | `bool` |
| `has(key)` | Check if key exists | `bool` |
| `merge(other)` | Deep merge another datastore | `None` |
| `to_dict()` | Export as plain dictionary | `dict` |
| `save(path, indent=2)` | Save to JSON file | `None` |

### Path Introspection

| Method | Description | Returns |
|--------|-------------|---------|
| `list_paths(prefix='')` | List all paths | `List[str]` |
| `find_paths(pattern)` | Find paths matching pattern | `List[str]` |
| `get_many(paths)` | Get multiple values | `Dict[str, Any]` |

### Deep Search

| Method | Description | Returns |
|--------|-------------|---------|
| `find_all_keys(key)` | Find all occurrences of key | `Dict[str, Any]` |
| `find_values(predicate)` | Find values matching predicate | `Dict[str, Any]` |

### Bulk Operations

| Method | Description | Returns |
|--------|-------------|---------|
| `update_where(condition, transform)` | Update matching values | `int` |
| `remove_nulls()` | Remove all None values | `int` |
| `remove_empty()` | Remove empty dicts/lists | `int` |

### Query Builder

| Method | Description | Returns |
|--------|-------------|---------|
| `query(path)` | Start query builder | `QueryBuilder` |
| `.where(predicate)` | Filter items | `QueryBuilder` |
| `.sort(key, reverse=False)` | Sort results | `QueryBuilder` |
| `.limit(count)` | Limit results | `QueryBuilder` |
| `.offset(count)` | Skip results | `QueryBuilder` |
| `.execute()` | Run query | `List[Any]` |
| `.count()` | Count results | `int` |
| `.first()` | Get first result | `Any \| None` |
| `.pluck(key)` | Extract field values | `List[Any]` |
| `.group_by(key)` | Group by field | `dict` |

### Transformations

| Method | Description | Returns |
|--------|-------------|---------|
| `transform_all(fn)` | Transform all values | `NitroDataStore` |
| `transform_keys(fn)` | Transform all keys | `NitroDataStore` |

### Introspection

| Method | Description | Returns |
|--------|-------------|---------|
| `describe()` | Get structural description | `Dict[str, Any]` |
| `stats()` | Get statistics | `Dict[str, int]` |

### Comparison

| Method | Description | Returns |
|--------|-------------|---------|
| `equals(other)` | Check equality | `bool` |
| `diff(other)` | Find differences | `Dict[str, Any]` |

### Iteration

| Method | Description | Returns |
|--------|-------------|---------|
| `keys()` | Get top-level keys | `Iterator[str]` |
| `values()` | Get top-level values | `Iterator[Any]` |
| `items()` | Get top-level items | `Iterator[tuple]` |
| `flatten(separator='.')` | Flatten to dot-notation | `dict` |

### Collection Utilities

| Method | Description | Returns |
|--------|-------------|---------|
| `filter_list(path, predicate)` | Filter list at path | `List[Any]` |

## Practical Examples

### Example 1: Data Cleaning Pipeline

```python
# Load messy data
data = NitroDataStore.from_file('messy_data.json')

# Clean it up
data.remove_nulls()
data.remove_empty()

# Standardize URLs
data.update_where(
    lambda p, v: isinstance(v, str) and 'http://' in v,
    lambda v: v.replace('http://', 'https://')
)

# Save cleaned data
data.save('cleaned_data.json')
```

### Example 2: Blog Post Querying

```python
blog = NitroDataStore.from_directory('content/posts/')

# Get recent published posts
recent = (blog.query('posts')
    .where(lambda p: p.get('published'))
    .sort(key=lambda p: p.get('date'), reverse=True)
    .limit(10)
    .execute())

# Get all unique categories
categories = set(blog.query('posts').pluck('category'))
```

### Example 3: Configuration Migration

```python
old_config = NitroDataStore.from_file('old_config.json')

# Transform to new schema
new_config = old_config.transform_keys(lambda k: k.replace('_', '-'))

# Detect changes
changes = old_config.diff(new_config)
print(f"Changed {len(changes['changed'])} keys")

new_config.save('new_config.json')
```

### Example 4: Data Discovery

```python
data = NitroDataStore.from_file('unknown_structure.json')

# Understand the structure
print("Stats:", data.stats())
print("Description:", data.describe())

# Find specific data
emails = data.find_values(lambda v: isinstance(v, str) and '@' in v)
images = data.find_values(lambda v: isinstance(v, str) and v.endswith(('.jpg', '.png')))
```

## Performance Tips

1. **Use query builder for collections** - Much faster than manual filtering
2. **Use find_paths() for pattern matching** - More efficient than manual traversal
3. **Batch updates with update_where()** - Single pass through data
4. **Use count() instead of len(execute())** - Skips result collection
5. **Load data once and reuse** - Avoid repeated file I/O

## License

MIT License - Part of the Nitro CLI project.

## See Also

- [Nitro CLI Documentation](https://github.com/nitro-sh/nitro-cli)
- [YDNATL Documentation](https://github.com/sn/ydnatl)
- [Advanced Features Guide](docs/DATASTORE_NEW_FEATURES.md)