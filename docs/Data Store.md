# NitroDataStore Guide

NitroDataStore is a flexible data management class for working with JSON and YAML data files in your Nitro projects. It provides multiple access patterns and powerful features for managing structured data.

## Table of Contents

- [Quick Start](#quick-start)
- [Creating a DataStore](#creating-a-datastore)
- [Access Patterns](#access-patterns)
- [File Operations](#file-operations)
- [Data Manipulation](#data-manipulation)
- [Integration with Nitro Pages](#integration-with-nitro-pages)
- [Advanced Features](#advanced-features)
- [API Reference](#api-reference)

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

# Access with dot notation
print(data.site.name)  # "My Awesome Site"

# Access with dictionary syntax
print(data['site']['url'])  # "https://example.com"

# Access with path notation
print(data.get('site.name'))  # "My Awesome Site"
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
# Load from a single JSON file
data = NitroDataStore.from_file('data/config.json')
```

**data/config.json:**
```json
{
  "site": {
    "name": "My Site",
    "tagline": "Building great things"
  },
  "social": {
    "twitter": "@mysite",
    "github": "mysite"
  }
}
```

### From a Directory (Auto-merge)

```python
# Load and merge all JSON files in a directory
data = NitroDataStore.from_directory('data/')
```

Files are merged alphabetically. Later files override earlier ones:

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

Result:
```python
data.site.name  # "Updated Site Name" (overridden by theme.json)
data.site.url   # "https://example.com" (preserved from site.json)
data.theme.colors.primary  # "#007bff" (added by theme.json)
```

## Access Patterns

NitroDataStore supports multiple access patterns - use whichever feels most natural for your code:

### 1. Dot Notation (Recommended)

```python
data = NitroDataStore({
    'user': {
        'name': 'Alice',
        'email': 'alice@example.com',
        'settings': {
            'notifications': True
        }
    }
})

# Read values
print(data.user.name)  # "Alice"
print(data.user.settings.notifications)  # True

# Set values
data.user.name = 'Bob'
data.user.settings.theme = 'dark'
```

### 2. Dictionary Access

```python
# Read values
print(data['user']['name'])  # "Bob"
print(data['user']['settings']['theme'])  # "dark"

# Set values
data['user']['email'] = 'bob@example.com'

# Check existence
if 'user' in data:
    print("User data exists")

# Delete keys
del data['user']['settings']['theme']
```

### 3. Path-based Access (Best for dynamic paths)

```python
# Get with default values
name = data.get('user.name', 'Anonymous')
theme = data.get('user.settings.theme', 'light')

# Set nested values (creates intermediate dicts)
data.set('config.cache.ttl', 3600)
data.set('config.cache.enabled', True)

# Delete nested values
deleted = data.delete('config.cache.ttl')  # Returns True if deleted

# Check existence
if data.has('user.settings.notifications'):
    print("Notifications setting exists")
```

## File Operations

### Loading Data

```python
# Load from JSON file
config = NitroDataStore.from_file('config.json')

# Load from directory with custom pattern
data = NitroDataStore.from_directory('data/', pattern='*.config.json')

# Using load_data() helper (automatically wraps in NitroDataStore)
from nitro import load_data

data = load_data('data/site.json')  # Returns NitroDataStore
data = load_data('data/', wrap=True)  # Directory loading
data = load_data('data/site.json', wrap=False)  # Returns plain dict
```

### Saving Data

```python
data = NitroDataStore({
    'site': {'name': 'My Site'},
    'version': '1.0.0'
})

# Save to JSON file (creates parent directories if needed)
data.save('output/config.json')

# Custom indentation
data.save('output/config.json', indent=4)
```

## Data Manipulation

### Setting Values

```python
data = NitroDataStore()

# Simple values
data.set('title', 'My Page')
data.set('count', 42)
data.set('enabled', True)

# Nested values (auto-creates intermediate dicts)
data.set('config.theme.colors.primary', '#007bff')
data.set('config.theme.colors.secondary', '#6c757d')

# Lists and complex structures
data.set('tags', ['python', 'web', 'static-site'])
data.set('meta.authors', [
    {'name': 'Alice', 'role': 'Developer'},
    {'name': 'Bob', 'role': 'Designer'}
])
```

### Merging Data

```python
base = NitroDataStore({
    'site': {
        'name': 'Original Name',
        'url': 'https://example.com'
    }
})

updates = NitroDataStore({
    'site': {
        'name': 'New Name'  # This will override
    },
    'theme': 'dark'  # This will be added
})

base.merge(updates)

print(base.site.name)  # "New Name" (updated)
print(base.site.url)   # "https://example.com" (preserved)
print(base.theme)      # "dark" (added)
```

### Iteration

```python
data = NitroDataStore({
    'title': 'Home',
    'author': 'Alice',
    'published': True
})

# Iterate over keys
for key in data.keys():
    print(key)

# Iterate over values
for value in data.values():
    print(value)

# Iterate over items
for key, value in data.items():
    print(f"{key}: {value}")
```

### Flattening

```python
data = NitroDataStore({
    'site': {
        'name': 'My Site',
        'settings': {
            'theme': 'dark',
            'language': 'en'
        }
    }
})

flat = data.flatten()
# {
#     'site.name': 'My Site',
#     'site.settings.theme': 'dark',
#     'site.settings.language': 'en'
# }

# Custom separator
flat = data.flatten(separator='/')
# {
#     'site/name': 'My Site',
#     'site/settings/theme': 'dark',
#     'site/settings/language': 'en'
# }
```

### Exporting

```python
data = NitroDataStore({'site': {'name': 'Test'}})

# Export as plain dictionary (deep copy)
plain_dict = data.to_dict()

# Modify the copy (doesn't affect original)
plain_dict['site']['name'] = 'Modified'
print(data.site.name)  # Still "Test"

# Pretty print
print(str(data))  # JSON formatted string
print(repr(data))  # NitroDataStore({'site': {'name': 'Test'}})
```

## Integration with Nitro Pages

### Using in Page Files

**src/data/site.json:**
```json
{
  "site": {
    "name": "My Portfolio",
    "tagline": "Building amazing things",
    "author": "Alice Developer"
  },
  "social": {
    "github": "alice",
    "twitter": "@alice"
  }
}
```

**src/pages/index.py:**
```python
from ydnatl import HTML, Head, Body, H1, Paragraph, Link, Footer
from nitro import Page, load_data

def render():
    # Load data (automatically wrapped in NitroDataStore)
    site_data = load_data('data/site.json')

    # Access with dot notation
    page = HTML(
        Head(
            title=f"{site_data.site.name} - {site_data.site.tagline}"
        ),
        Body(
            H1(site_data.site.name),
            Paragraph(site_data.site.tagline),
            Paragraph(f"By {site_data.site.author}"),
            Footer(
                Link('GitHub', href=f"https://github.com/{site_data.social.github}"),
                " | ",
                Link('Twitter', href=f"https://twitter.com/{site_data.social.twitter}")
            )
        )
    )

    return Page(
        title=site_data.site.name,
        content=page,
        meta={
            'description': site_data.site.tagline,
            'author': site_data.site.author
        }
    )
```

### Loading Multiple Data Sources

```python
from nitro import Page, load_data, NitroDataStore

def render():
    # Load site configuration
    site = load_data('data/site.json')

    # Load blog posts
    posts = load_data('data/posts.json')

    # Load from directory (merges all files)
    config = load_data('data/config/')

    # Manual creation
    page_data = NitroDataStore({
        'title': 'Blog',
        'posts_count': len(posts.get('posts', []))
    })

    # Merge data sources
    combined = NitroDataStore()
    combined.merge(site)
    combined.merge(config)
    combined.merge(page_data)

    # Use combined data
    # ...
```

### Dynamic Data Access

```python
from nitro import load_data

def render():
    data = load_data('data/site.json')

    # Get with defaults (safe for missing keys)
    title = data.get('site.title', 'Untitled')
    author = data.get('site.author', 'Anonymous')
    theme = data.get('theme.colors.primary', '#000000')

    # Check before accessing
    if data.has('featured.post'):
        featured = data.get('featured.post')
    else:
        featured = None

    # Safe iteration
    social_links = []
    if data.has('social'):
        for platform, handle in data.social.items():
            social_links.append(f"{platform}: {handle}")

    # ...
```

## Advanced Features

### Chained Access

```python
data = NitroDataStore({
    'config': {
        'theme': {
            'colors': {
                'primary': '#007bff',
                'secondary': '#6c757d'
            }
        }
    }
})

# All of these work and return the same value
print(data.config.theme.colors.primary)          # Dot notation
print(data['config']['theme']['colors']['primary'])  # Dict access
print(data.get('config.theme.colors.primary'))    # Path access
```

### Modifying Nested DataStores

```python
data = NitroDataStore({
    'user': {
        'profile': {
            'name': 'Alice'
        }
    }
})

# Get nested datastore
profile = data.user.profile

# Modifications affect the original
profile.name = 'Bob'
profile.email = 'bob@example.com'

print(data.get('user.profile.name'))  # "Bob"
print(data.get('user.profile.email'))  # "bob@example.com"
```

### Type Preservation

```python
data = NitroDataStore({
    'string': 'text',
    'number': 42,
    'float': 3.14,
    'boolean': True,
    'null': None,
    'list': [1, 2, 3],
    'dict': {'nested': 'value'}
})

# Types are preserved
assert isinstance(data.string, str)
assert isinstance(data.number, int)
assert isinstance(data.float, float)
assert isinstance(data.boolean, bool)
assert data.null is None
assert isinstance(data.list, list)
# Nested dicts are wrapped
assert isinstance(data.dict, NitroDataStore)
```

### Unicode and Special Characters

```python
data = NitroDataStore({
    'unicode': {
        'emoji': '🚀',
        'japanese': '日本語',
        'chinese': '中文'
    },
    'special-keys': {
        'key-with-dashes': 'value1',
        'key_with_underscores': 'value2'
    }
})

print(data.unicode.emoji)  # "🚀"
print(data['special-keys']['key-with-dashes'])  # "value1"
```

## API Reference

### Initialization

```python
NitroDataStore(data: Dict = None)
```

Create a new datastore from a dictionary.

### Class Methods

```python
NitroDataStore.from_file(file_path: Path | str) -> NitroDataStore
```
Load from a JSON file.

```python
NitroDataStore.from_directory(directory: Path | str, pattern: str = "*.json") -> NitroDataStore
```
Load and merge all JSON files from a directory.

### Instance Methods

#### Access Methods

```python
get(key: str, default: Any = None) -> Any
```
Get value using dot notation path.

```python
set(key: str, value: Any) -> None
```
Set value using dot notation path.

```python
delete(key: str) -> bool
```
Delete value using dot notation path. Returns True if deleted.

```python
has(key: str) -> bool
```
Check if key exists using dot notation path.

#### Data Operations

```python
merge(other: NitroDataStore | Dict) -> None
```
Deep merge another datastore or dictionary.

```python
to_dict() -> Dict
```
Export as plain dictionary (deep copy).

```python
flatten(separator: str = '.') -> Dict
```
Flatten nested structure to dot-notation keys.

#### File Operations

```python
save(file_path: Path | str, indent: int = 2) -> None
```
Save data to JSON file.

#### Iteration

```python
keys() -> Iterator[str]
```
Get top-level keys.

```python
values() -> Iterator[Any]
```
Get top-level values.

```python
items() -> Iterator[tuple]
```
Get top-level key-value pairs.

### Special Methods

```python
data['key']          # __getitem__ - Dictionary access
data['key'] = value  # __setitem__ - Dictionary assignment
del data['key']      # __delitem__ - Dictionary deletion
'key' in data        # __contains__ - Membership test
len(data)            # __len__ - Number of top-level keys
data.key             # __getattr__ - Dot notation access
data.key = value     # __setattr__ - Dot notation assignment
str(data)            # __str__ - JSON string representation
repr(data)           # __repr__ - Debug representation
```

## Best Practices

1. **Use dot notation for static keys:**
   ```python
   # Good - clear and concise
   data.site.name

   # Less ideal for static keys
   data.get('site.name')
   ```

2. **Use path-based get() for dynamic keys:**
   ```python
   # Good - safe with defaults
   key = f"user.{user_id}.name"
   name = data.get(key, 'Unknown')

   # Risky - may raise AttributeError
   name = getattr(data.user, user_id).name
   ```

3. **Load data once, reuse across functions:**
   ```python
   # Load at module level
   SITE_DATA = load_data('data/site.json')

   def render():
       # Reuse loaded data
       return Page(
           title=SITE_DATA.site.name,
           # ...
       )
   ```

4. **Merge configuration hierarchically:**
   ```python
   # Base config
   config = load_data('data/defaults.json')

   # Environment overrides
   if env == 'production':
       config.merge(load_data('data/production.json'))

   # User overrides
   if user_config_exists:
       config.merge(load_data('data/user-config.json'))
   ```

5. **Use has() before accessing optional data:**
   ```python
   # Good - safe
   if data.has('featured.image'):
       image = data.get('featured.image')

   # Risky - may raise error
   image = data.featured.image
   ```

## Examples

See the `examples/` directory for complete working examples:

- `examples/blog-with-datastore/` - Blog site using NitroDataStore
- `examples/portfolio/` - Portfolio with configuration management
- `examples/multi-language/` - Multi-language site with data merging

## Troubleshooting

### KeyError: 'key'

Using dictionary access on missing keys raises KeyError:
```python
# This raises KeyError if 'missing' doesn't exist
value = data['missing']

# Use get() with default instead
value = data.get('missing', 'default')
```

### AttributeError: 'NitroDataStore' object has no attribute 'key'

Using dot notation on missing keys raises AttributeError:
```python
# This raises AttributeError if 'missing' doesn't exist
value = data.missing

# Check first or use get()
if data.has('missing'):
    value = data.missing
else:
    value = 'default'
```

### Modifications not persisting

Remember to call save() to persist changes to disk:
```python
data = NitroDataStore.from_file('config.json')
data.site.name = 'New Name'
# Changes are in memory only

data.save('config.json')  # Now persisted to disk
```