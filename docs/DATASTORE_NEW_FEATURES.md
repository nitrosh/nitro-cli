# NitroDataStore Advanced Features

This document covers the new advanced features added to NitroDataStore for schema-agnostic data manipulation.

## Table of Contents

- [Path Introspection](#path-introspection)
- [Deep Search](#deep-search)
- [Bulk Operations](#bulk-operations)
- [Data Introspection](#data-introspection)
- [Query Builder](#query-builder)
- [Transformations](#transformations)
- [Comparison](#comparison)

## Path Introspection

Discover and work with paths in your data structure without knowing the schema in advance.

### list_paths()

List all paths in the data structure.

```python
data = NitroDataStore({
    'site': {'name': 'My Site', 'url': 'example.com'},
    'posts': [{'title': 'Post 1'}, {'title': 'Post 2'}]
})

paths = data.list_paths()
# Returns: ['site', 'site.name', 'site.url', 'posts', 'posts.0', 'posts.0.title', 'posts.1', 'posts.1.title']

# Filter by prefix
site_paths = data.list_paths(prefix='site')
# Returns: ['site', 'site.name', 'site.url']
```

### find_paths()

Find paths matching glob-like patterns with wildcards.

```python
data = NitroDataStore({
    'posts': [
        {'title': 'Post 1', 'author': 'Alice'},
        {'title': 'Post 2', 'author': 'Bob'}
    ]
})

# Find all titles
titles = data.find_paths('posts.*.title')
# Returns: ['posts.0.title', 'posts.1.title']

# Find all 'author' keys anywhere
authors = data.find_paths('**.author')
# Returns: ['posts.0.author', 'posts.1.author']
```

**Wildcard Patterns:**
- `*` - Matches any single path segment
- `**` - Matches any number of path segments

### get_many()

Get multiple values by their paths in one call.

```python
data = NitroDataStore({
    'site': {'name': 'My Site', 'url': 'example.com'},
    'theme': 'dark'
})

values = data.get_many(['site.name', 'site.url', 'theme', 'missing.key'])
# Returns: {
#     'site.name': 'My Site',
#     'site.url': 'example.com',
#     'theme': 'dark',
#     'missing.key': None
# }
```

## Deep Search

Find values anywhere in your data structure based on criteria.

### find_all_keys()

Find all occurrences of a specific key name throughout the structure.

```python
data = NitroDataStore({
    'site': {'url': 'site.com', 'name': 'Main Site'},
    'social': {
        'github': {'url': 'github.com/user'},
        'twitter': {'url': 'twitter.com/user'}
    }
})

urls = data.find_all_keys('url')
# Returns: {
#     'site.url': 'site.com',
#     'social.github.url': 'github.com/user',
#     'social.twitter.url': 'twitter.com/user'
# }
```

### find_values()

Find all values matching a predicate function.

```python
data = NitroDataStore({
    'images': {
        'hero': 'banner.jpg',
        'thumbnail': 'thumb.png',
        'background': 'bg.jpg'
    },
    'count': 42
})

# Find all .jpg images
jpgs = data.find_values(lambda v: isinstance(v, str) and v.endswith('.jpg'))
# Returns: {'images.hero': 'banner.jpg', 'images.background': 'bg.jpg'}

# Find all numbers greater than 10
big_numbers = data.find_values(lambda v: isinstance(v, (int, float)) and v > 10)
# Returns: {'count': 42}
```

## Bulk Operations

Perform operations on multiple values at once.

### update_where()

Update all values matching a condition.

```python
data = NitroDataStore({
    'pages': {
        'home': 'http://example.com/home',
        'about': 'http://example.com/about'
    },
    'external': ['http://other.com', 'https://secure.com']
})

# Upgrade all HTTP URLs to HTTPS
count = data.update_where(
    condition=lambda path, value: isinstance(value, str) and 'http://' in value,
    transform=lambda value: value.replace('http://', 'https://')
)
# Returns: 3 (number of values updated)
```

### remove_nulls()

Remove all `None` values from the data structure.

```python
data = NitroDataStore({
    'user': {'name': 'Alice', 'email': None},
    'settings': {'theme': 'dark', 'language': None},
    'items': [1, None, 2, None, 3]
})

count = data.remove_nulls()
# Returns: 3

# Result:
# {
#     'user': {'name': 'Alice'},
#     'settings': {'theme': 'dark'},
#     'items': [1, 2, 3]
# }
```

### remove_empty()

Remove all empty dictionaries and lists.

```python
data = NitroDataStore({
    'config': {},
    'tags': [],
    'nested': {'value': 1, 'empty': {}},
    'items': [[], [1], []]
})

count = data.remove_empty()
# Returns: 4 (empty containers removed)

# Result:
# {
#     'nested': {'value': 1},
#     'items': [[1]]
# }
```

## Data Introspection

Understand the structure of your data.

### describe()

Get a structural description of the data.

```python
data = NitroDataStore({
    'site': {'name': 'My Site', 'year': 2024},
    'posts': [{'title': 'Post 1'}, {'title': 'Post 2'}],
    'active': True
})

description = data.describe()
# Returns: {
#     'site': {
#         'type': 'dict',
#         'keys': ['name', 'year'],
#         'structure': {
#             'name': {'type': 'str', 'value': 'My Site'},
#             'year': {'type': 'int', 'value': 2024}
#         }
#     },
#     'posts': {
#         'type': 'list',
#         'length': 2,
#         'item_types': ['dict']
#     },
#     'active': {
#         'type': 'bool',
#         'value': True
#     }
# }
```

### stats()

Get statistics about the data structure.

```python
data = NitroDataStore({
    'level1': {
        'level2': {
            'level3': 'value'
        }
    },
    'items': [1, 2, 3]
})

stats = data.stats()
# Returns: {
#     'total_keys': 3,
#     'max_depth': 3,
#     'total_dicts': 3,
#     'total_lists': 1,
#     'total_values': 4
# }
```

## Query Builder

Chainable query interface for filtering and transforming collections.

### Basic Querying

```python
data = NitroDataStore({
    'posts': [
        {'title': 'Python Tips', 'category': 'python', 'views': 150, 'published': True},
        {'title': 'Web Dev', 'category': 'web', 'views': 200, 'published': True},
        {'title': 'Draft Post', 'category': 'python', 'views': 0, 'published': False}
    ]
})

# Get all published posts
published = data.query('posts').where(lambda p: p.get('published')).execute()
```

### where()

Filter items with a predicate function.

```python
# Multiple where clauses (AND logic)
popular_python = (data.query('posts')
    .where(lambda p: p.get('category') == 'python')
    .where(lambda p: p.get('views') > 100)
    .execute())
```

### sort()

Sort results by a key function.

```python
# Sort by views (ascending)
by_views = data.query('posts').sort(key=lambda p: p.get('views')).execute()

# Sort by views (descending)
popular_first = data.query('posts').sort(key=lambda p: p.get('views'), reverse=True).execute()
```

### limit() and offset()

Pagination support.

```python
# First 10 posts
first_page = data.query('posts').limit(10).execute()

# Next 10 posts
second_page = data.query('posts').offset(10).limit(10).execute()
```

### Chaining Operations

```python
# Complex query: published Python posts, sorted by views, top 5
top_python = (data.query('posts')
    .where(lambda p: p.get('category') == 'python')
    .where(lambda p: p.get('published'))
    .sort(key=lambda p: p.get('views'), reverse=True)
    .limit(5)
    .execute())
```

### count()

Count results without fetching all data.

```python
# How many published posts?
published_count = (data.query('posts')
    .where(lambda p: p.get('published'))
    .count())
```

### first()

Get just the first result.

```python
# Get most popular post
most_popular = (data.query('posts')
    .sort(key=lambda p: p.get('views'), reverse=True)
    .first())
```

### pluck()

Extract a single field from all results.

```python
# Get all titles
titles = data.query('posts').pluck('title')
# Returns: ['Python Tips', 'Web Dev', 'Draft Post']
```

### group_by()

Group results by a field value.

```python
# Group by category
by_category = data.query('posts').group_by('category')
# Returns: {
#     'python': [{'title': 'Python Tips', ...}, {'title': 'Draft Post', ...}],
#     'web': [{'title': 'Web Dev', ...}]
# }
```

## Transformations

Create new datastores with transformed data.

### transform_all()

Transform all values based on path and value.

```python
data = NitroDataStore({
    'user': {'name': 'alice', 'email': 'alice@example.com'},
    'settings': {'theme': 'dark'}
})

# Uppercase all strings
uppercase = data.transform_all(
    lambda path, value: value.upper() if isinstance(value, str) else value
)

# Result:
# {
#     'user': {'name': 'ALICE', 'email': 'ALICE@EXAMPLE.COM'},
#     'settings': {'theme': 'DARK'}
# }

# Original unchanged
print(data.user.name)  # 'alice'
```

### transform_keys()

Transform all keys throughout the structure.

```python
data = NitroDataStore({
    'user-info': {
        'first-name': 'John',
        'last-name': 'Doe'
    },
    'contact-email': 'john@example.com'
})

# Convert kebab-case to snake_case
snake_case = data.transform_keys(lambda k: k.replace('-', '_'))

# Result:
# {
#     'user_info': {
#         'first_name': 'John',
#         'last_name': 'Doe'
#     },
#     'contact_email': 'john@example.com'
# }
```

## Comparison

Compare datastores and detect differences.

### equals()

Check if two datastores are equal.

```python
data1 = NitroDataStore({'name': 'Alice', 'age': 30})
data2 = NitroDataStore({'name': 'Alice', 'age': 30})
data3 = NitroDataStore({'name': 'Bob', 'age': 25})

print(data1.equals(data2))  # True
print(data1.equals(data3))  # False

# Also works with plain dicts
print(data1.equals({'name': 'Alice', 'age': 30}))  # True
```

### diff()

Find differences between two datastores.

```python
old_config = NitroDataStore({
    'site': {'name': 'Old Name', 'url': 'example.com'},
    'theme': 'light',
    'version': '1.0'
})

new_config = NitroDataStore({
    'site': {'name': 'New Name', 'url': 'example.com'},
    'theme': 'dark',
    'features': ['comments', 'search']
})

diff = old_config.diff(new_config)

# diff['added']: New keys
# {'features': ['comments', 'search']}

# diff['removed']: Removed keys
# {'version': '1.0'}

# diff['changed']: Changed values
# {
#     'site.name': {'old': 'Old Name', 'new': 'New Name'},
#     'theme': {'old': 'light', 'new': 'dark'}
# }
```

## Practical Examples

### Example 1: Data Cleaning Pipeline

```python
# Load messy data
data = NitroDataStore.from_file('messy_data.json')

# Clean it up
data.remove_nulls()  # Remove all None values
data.remove_empty()  # Remove empty dicts/lists

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
recent_posts = (blog.query('posts')
    .where(lambda p: p.get('published'))
    .sort(key=lambda p: p.get('date'), reverse=True)
    .limit(10)
    .execute())

# Get posts by category
python_posts = blog.filter_list('posts', lambda p: p.get('category') == 'python')

# Get all unique categories
all_categories = set(blog.query('posts').pluck('category'))
```

### Example 3: Configuration Migration

```python
old_config = NitroDataStore.from_file('old_config.json')

# Transform to new schema
new_config = old_config.transform_keys(lambda k: k.replace('_', '-'))

# Detect what changed
changes = old_config.diff(new_config)
print(f"Changed {len(changes['changed'])} keys")

# Save new config
new_config.save('new_config.json')
```

### Example 4: Data Discovery

```python
data = NitroDataStore.from_file('unknown_structure.json')

# Understand the structure
print("Statistics:", data.stats())
print("Description:", data.describe())

# Find all paths
all_paths = data.list_paths()
print(f"Total paths: {len(all_paths)}")

# Find all email addresses
emails = data.find_values(lambda v: isinstance(v, str) and '@' in v)
print("Email addresses:", emails)

# Find all image files
images = data.find_values(lambda v: isinstance(v, str) and v.endswith(('.jpg', '.png', '.gif')))
print("Images:", images)
```

## Performance Tips

1. **Use query builder for collections**: Much faster than manual filtering
2. **Use find_paths() for pattern matching**: More efficient than manual traversal
3. **Batch updates with update_where()**: Single pass through data
4. **Use count() instead of len(execute())**: Skips result collection

## API Quick Reference

| Method | Description | Returns |
|--------|-------------|---------|
| `list_paths(prefix='')` | List all paths in structure | `List[str]` |
| `find_paths(pattern)` | Find paths matching pattern | `List[str]` |
| `get_many(paths)` | Get multiple values at once | `Dict[str, Any]` |
| `find_all_keys(key)` | Find all occurrences of key name | `Dict[str, Any]` |
| `find_values(predicate)` | Find values matching predicate | `Dict[str, Any]` |
| `update_where(condition, transform)` | Update matching values | `int` |
| `remove_nulls()` | Remove all None values | `int` |
| `remove_empty()` | Remove empty dicts/lists | `int` |
| `describe()` | Get structural description | `Dict[str, Any]` |
| `stats()` | Get structure statistics | `Dict[str, int]` |
| `query(path)` | Start query builder | `QueryBuilder` |
| `transform_all(fn)` | Transform all values | `NitroDataStore` |
| `transform_keys(fn)` | Transform all keys | `NitroDataStore` |
| `diff(other)` | Find differences | `Dict[str, Any]` |
| `equals(other)` | Check equality | `bool` |
| `filter_list(path, predicate)` | Filter list at path | `List[Any]` |
