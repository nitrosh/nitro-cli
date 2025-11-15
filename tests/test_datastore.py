"""Comprehensive tests for NitroDataStore."""

import json
import pytest
from pathlib import Path
from nitro.core.datastore import NitroDataStore


class TestNitroDataStoreInit:
    """Test initialization."""

    def test_init_empty(self):
        """Test initializing with no data."""
        data = NitroDataStore()
        assert len(data) == 0
        assert data.to_dict() == {}

    def test_init_with_data(self):
        """Test initializing with data."""
        initial = {'site': {'name': 'My Site', 'url': 'example.com'}}
        data = NitroDataStore(initial)
        assert len(data) == 1
        assert data.to_dict() == initial

    def test_init_with_none(self):
        """Test initializing with None explicitly."""
        data = NitroDataStore(None)
        assert len(data) == 0
        assert data.to_dict() == {}


class TestNitroDataStoreFileOperations:
    """Test file loading and saving."""

    def test_from_file_valid(self, tmp_path):
        """Test loading from a valid JSON file."""
        test_data = {'site': {'name': 'Test Site', 'version': 1}}
        json_file = tmp_path / "data.json"
        json_file.write_text(json.dumps(test_data))

        data = NitroDataStore.from_file(json_file)
        assert data.to_dict() == test_data

    def test_from_file_not_found(self):
        """Test loading from non-existent file."""
        with pytest.raises(FileNotFoundError):
            NitroDataStore.from_file("nonexistent.json")

    def test_from_file_invalid_json(self, tmp_path):
        """Test loading from file with invalid JSON."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            NitroDataStore.from_file(json_file)

    def test_from_directory_single_file(self, tmp_path):
        """Test loading from directory with single file."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        test_data = {'site': {'name': 'Site 1'}}
        (data_dir / "data1.json").write_text(json.dumps(test_data))

        data = NitroDataStore.from_directory(data_dir)
        assert data.to_dict() == test_data

    def test_from_directory_multiple_files_merge(self, tmp_path):
        """Test loading from directory merges files correctly."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        # Files are merged in alphabetical order
        (data_dir / "a.json").write_text(json.dumps({'site': {'name': 'Site A', 'url': 'a.com'}}))
        (data_dir / "b.json").write_text(json.dumps({'site': {'name': 'Site B'}, 'extra': 'data'}))

        data = NitroDataStore.from_directory(data_dir)
        result = data.to_dict()

        # b.json should override site.name from a.json
        assert result['site']['name'] == 'Site B'
        # But site.url from a.json should remain
        assert result['site']['url'] == 'a.com'
        # And extra from b.json should be present
        assert result['extra'] == 'data'

    def test_from_directory_not_found(self):
        """Test loading from non-existent directory."""
        with pytest.raises(FileNotFoundError):
            NitroDataStore.from_directory("nonexistent_dir")

    def test_from_directory_skips_invalid_json(self, tmp_path):
        """Test that invalid JSON files are skipped during directory load."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        (data_dir / "valid.json").write_text(json.dumps({'valid': 'data'}))
        (data_dir / "invalid.json").write_text("{ invalid }")

        data = NitroDataStore.from_directory(data_dir)
        assert data.to_dict() == {'valid': 'data'}

    def test_from_directory_custom_pattern(self, tmp_path):
        """Test loading from directory with custom pattern."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        (data_dir / "config.json").write_text(json.dumps({'config': 'data'}))
        (data_dir / "data.txt").write_text(json.dumps({'txt': 'data'}))

        # Only load .json files
        data = NitroDataStore.from_directory(data_dir, pattern="*.json")
        assert 'config' in data.to_dict()
        assert 'txt' not in data.to_dict()

    def test_save(self, tmp_path):
        """Test saving data to file."""
        data = NitroDataStore({'site': {'name': 'My Site'}})
        output_file = tmp_path / "output.json"

        data.save(output_file)

        assert output_file.exists()
        with open(output_file) as f:
            saved_data = json.load(f)
        assert saved_data == {'site': {'name': 'My Site'}}

    def test_save_creates_parent_dirs(self, tmp_path):
        """Test that save creates parent directories."""
        data = NitroDataStore({'test': 'data'})
        output_file = tmp_path / "nested" / "dirs" / "output.json"

        data.save(output_file)

        assert output_file.exists()
        assert output_file.parent.exists()

    def test_save_custom_indent(self, tmp_path):
        """Test saving with custom indentation."""
        data = NitroDataStore({'site': {'name': 'Test'}})
        output_file = tmp_path / "output.json"

        data.save(output_file, indent=4)

        content = output_file.read_text()
        # Check that indentation is 4 spaces
        assert '    "site"' in content


class TestNitroDataStoreGet:
    """Test get operations."""

    def test_get_simple_key(self):
        """Test getting a simple top-level key."""
        data = NitroDataStore({'name': 'Test'})
        assert data.get('name') == 'Test'

    def test_get_nested_key(self):
        """Test getting nested key with dot notation."""
        data = NitroDataStore({'site': {'name': 'My Site', 'url': 'example.com'}})
        assert data.get('site.name') == 'My Site'
        assert data.get('site.url') == 'example.com'

    def test_get_deeply_nested_key(self):
        """Test getting deeply nested key."""
        data = NitroDataStore({
            'config': {
                'theme': {
                    'colors': {
                        'primary': '#007bff'
                    }
                }
            }
        })
        assert data.get('config.theme.colors.primary') == '#007bff'

    def test_get_missing_key_returns_none(self):
        """Test that missing key returns None."""
        data = NitroDataStore({'name': 'Test'})
        assert data.get('missing') is None

    def test_get_missing_nested_key_returns_none(self):
        """Test that missing nested key returns None."""
        data = NitroDataStore({'site': {'name': 'Test'}})
        assert data.get('site.missing') is None
        assert data.get('missing.nested.key') is None

    def test_get_with_default(self):
        """Test get with default value."""
        data = NitroDataStore({'name': 'Test'})
        assert data.get('missing', 'default') == 'default'
        assert data.get('site.missing', 'fallback') == 'fallback'

    def test_get_returns_various_types(self):
        """Test that get returns correct types."""
        data = NitroDataStore({
            'string': 'text',
            'number': 42,
            'float': 3.14,
            'bool': True,
            'list': [1, 2, 3],
            'dict': {'nested': 'value'}
        })
        assert isinstance(data.get('string'), str)
        assert isinstance(data.get('number'), int)
        assert isinstance(data.get('float'), float)
        assert isinstance(data.get('bool'), bool)
        assert isinstance(data.get('list'), list)
        assert isinstance(data.get('dict'), dict)


class TestNitroDataStoreSet:
    """Test set operations."""

    def test_set_simple_key(self):
        """Test setting a simple key."""
        data = NitroDataStore()
        data.set('name', 'Test')
        assert data.get('name') == 'Test'

    def test_set_nested_key(self):
        """Test setting nested key with dot notation."""
        data = NitroDataStore()
        data.set('site.name', 'My Site')
        assert data.get('site.name') == 'My Site'

    def test_set_deeply_nested_key(self):
        """Test setting deeply nested key creates structure."""
        data = NitroDataStore()
        data.set('config.theme.colors.primary', '#007bff')
        assert data.get('config.theme.colors.primary') == '#007bff'

    def test_set_overwrites_existing(self):
        """Test that set overwrites existing values."""
        data = NitroDataStore({'name': 'Old'})
        data.set('name', 'New')
        assert data.get('name') == 'New'

    def test_set_overwrites_nested(self):
        """Test that set overwrites nested values."""
        data = NitroDataStore({'site': {'name': 'Old'}})
        data.set('site.name', 'New')
        assert data.get('site.name') == 'New'

    def test_set_creates_missing_intermediate_dicts(self):
        """Test that set creates missing intermediate dictionaries."""
        data = NitroDataStore()
        data.set('a.b.c.d', 'value')

        # All intermediate dicts should exist
        assert 'a' in data
        assert isinstance(data.to_dict()['a'], dict)
        assert 'b' in data.to_dict()['a']
        assert data.get('a.b.c.d') == 'value'

    def test_set_replaces_non_dict_with_dict(self):
        """Test that set replaces non-dict values when creating nested paths."""
        data = NitroDataStore({'site': 'string_value'})
        data.set('site.name', 'New Site')

        # 'site' should now be a dict
        assert isinstance(data.to_dict()['site'], dict)
        assert data.get('site.name') == 'New Site'

    def test_set_various_types(self):
        """Test setting various value types."""
        data = NitroDataStore()
        data.set('string', 'text')
        data.set('number', 42)
        data.set('float', 3.14)
        data.set('bool', True)
        data.set('list', [1, 2, 3])
        data.set('dict', {'nested': 'value'})

        assert data.get('string') == 'text'
        assert data.get('number') == 42
        assert data.get('float') == 3.14
        assert data.get('bool') is True
        assert data.get('list') == [1, 2, 3]
        assert data.get('dict') == {'nested': 'value'}


class TestNitroDataStoreDelete:
    """Test delete operations."""

    def test_delete_simple_key(self):
        """Test deleting a simple key."""
        data = NitroDataStore({'name': 'Test', 'other': 'value'})
        result = data.delete('name')
        assert result is True
        assert 'name' not in data

    def test_delete_nested_key(self):
        """Test deleting nested key."""
        data = NitroDataStore({'site': {'name': 'Test', 'url': 'example.com'}})
        result = data.delete('site.name')
        assert result is True
        assert data.get('site.name') is None
        assert data.get('site.url') == 'example.com'  # Other keys remain

    def test_delete_missing_key_returns_false(self):
        """Test deleting non-existent key returns False."""
        data = NitroDataStore({'name': 'Test'})
        result = data.delete('missing')
        assert result is False

    def test_delete_missing_nested_key_returns_false(self):
        """Test deleting non-existent nested key returns False."""
        data = NitroDataStore({'site': {'name': 'Test'}})
        result = data.delete('site.missing')
        assert result is False
        result = data.delete('missing.nested.key')
        assert result is False

    def test_delete_already_deleted_returns_false(self):
        """Test deleting already deleted key returns False."""
        data = NitroDataStore({'name': 'Test'})
        assert data.delete('name') is True
        assert data.delete('name') is False


class TestNitroDataStoreHas:
    """Test has (existence check) operations."""

    def test_has_simple_key_exists(self):
        """Test checking simple key that exists."""
        data = NitroDataStore({'name': 'Test'})
        assert data.has('name') is True

    def test_has_simple_key_missing(self):
        """Test checking simple key that doesn't exist."""
        data = NitroDataStore({'name': 'Test'})
        assert data.has('missing') is False

    def test_has_nested_key_exists(self):
        """Test checking nested key that exists."""
        data = NitroDataStore({'site': {'name': 'Test'}})
        assert data.has('site.name') is True

    def test_has_nested_key_missing(self):
        """Test checking nested key that doesn't exist."""
        data = NitroDataStore({'site': {'name': 'Test'}})
        assert data.has('site.missing') is False
        assert data.has('missing.nested.key') is False

    def test_has_deeply_nested(self):
        """Test checking deeply nested keys."""
        data = NitroDataStore({'a': {'b': {'c': {'d': 'value'}}}})
        assert data.has('a.b.c.d') is True
        assert data.has('a.b.c.missing') is False


class TestNitroDataStoreMerge:
    """Test merge operations."""

    def test_merge_with_datastore(self):
        """Test merging with another NitroDataStore."""
        data1 = NitroDataStore({'site': {'name': 'Site 1', 'url': 'example.com'}})
        data2 = NitroDataStore({'site': {'name': 'Site 2'}, 'extra': 'data'})

        data1.merge(data2)

        # site.name should be overwritten
        assert data1.get('site.name') == 'Site 2'
        # site.url should remain
        assert data1.get('site.url') == 'example.com'
        # extra should be added
        assert data1.get('extra') == 'data'

    def test_merge_with_dict(self):
        """Test merging with a plain dictionary."""
        data = NitroDataStore({'site': {'name': 'Old'}})
        data.merge({'site': {'name': 'New', 'url': 'example.com'}})

        assert data.get('site.name') == 'New'
        assert data.get('site.url') == 'example.com'

    def test_merge_deep(self):
        """Test deep merging of nested structures."""
        data1 = NitroDataStore({
            'config': {
                'theme': {
                    'colors': {'primary': 'blue', 'secondary': 'green'}
                }
            }
        })
        data2 = NitroDataStore({
            'config': {
                'theme': {
                    'colors': {'primary': 'red'},
                    'font': 'Arial'
                }
            }
        })

        data1.merge(data2)

        # Primary color overwritten
        assert data1.get('config.theme.colors.primary') == 'red'
        # Secondary color preserved
        assert data1.get('config.theme.colors.secondary') == 'green'
        # Font added
        assert data1.get('config.theme.font') == 'Arial'

    def test_merge_empty(self):
        """Test merging empty datastore does nothing."""
        data = NitroDataStore({'name': 'Test'})
        data.merge(NitroDataStore())
        assert data.get('name') == 'Test'


class TestNitroDataStoreIteration:
    """Test iteration methods."""

    def test_keys(self):
        """Test keys() method."""
        data = NitroDataStore({'a': 1, 'b': 2, 'c': 3})
        keys = list(data.keys())
        assert set(keys) == {'a', 'b', 'c'}

    def test_values(self):
        """Test values() method."""
        data = NitroDataStore({'a': 1, 'b': 2, 'c': 3})
        values = list(data.values())
        assert set(values) == {1, 2, 3}

    def test_items(self):
        """Test items() method."""
        data = NitroDataStore({'a': 1, 'b': 2})
        items = list(data.items())
        assert set(items) == {('a', 1), ('b', 2)}

    def test_iteration_with_for_loop(self):
        """Test that datastore is iterable."""
        data = NitroDataStore({'a': 1, 'b': 2, 'c': 3})
        keys = []
        for key in data.keys():
            keys.append(key)
        assert set(keys) == {'a', 'b', 'c'}


class TestNitroDataStoreFlatten:
    """Test flatten operations."""

    def test_flatten_simple(self):
        """Test flattening simple nested structure."""
        data = NitroDataStore({'site': {'name': 'Test', 'url': 'example.com'}})
        flat = data.flatten()
        assert flat == {'site.name': 'Test', 'site.url': 'example.com'}

    def test_flatten_deeply_nested(self):
        """Test flattening deeply nested structure."""
        data = NitroDataStore({
            'a': {
                'b': {
                    'c': {
                        'd': 'value'
                    }
                }
            }
        })
        flat = data.flatten()
        assert flat == {'a.b.c.d': 'value'}

    def test_flatten_mixed(self):
        """Test flattening mixed structure."""
        data = NitroDataStore({
            'simple': 'value',
            'nested': {
                'key': 'value2',
                'deeper': {
                    'key': 'value3'
                }
            }
        })
        flat = data.flatten()
        assert flat == {
            'simple': 'value',
            'nested.key': 'value2',
            'nested.deeper.key': 'value3'
        }

    def test_flatten_custom_separator(self):
        """Test flattening with custom separator."""
        data = NitroDataStore({'site': {'name': 'Test'}})
        flat = data.flatten(separator='/')
        assert flat == {'site/name': 'Test'}

    def test_flatten_preserves_non_dict_values(self):
        """Test that flatten preserves lists and other non-dict values."""
        data = NitroDataStore({
            'site': {
                'tags': ['tag1', 'tag2'],
                'enabled': True,
                'count': 42
            }
        })
        flat = data.flatten()
        assert flat['site.tags'] == ['tag1', 'tag2']
        assert flat['site.enabled'] is True
        assert flat['site.count'] == 42


class TestNitroDataStoreDictAccess:
    """Test dictionary-style access."""

    def test_getitem(self):
        """Test __getitem__ (data['key'])."""
        data = NitroDataStore({'name': 'Test', 'count': 42})
        assert data['name'] == 'Test'
        assert data['count'] == 42

    def test_getitem_missing_raises_keyerror(self):
        """Test __getitem__ with missing key raises KeyError."""
        data = NitroDataStore({'name': 'Test'})
        with pytest.raises(KeyError):
            _ = data['missing']

    def test_getitem_returns_wrapped_dict(self):
        """Test __getitem__ wraps nested dicts in NitroDataStore."""
        data = NitroDataStore({'site': {'name': 'Test'}})
        site = data['site']
        assert isinstance(site, NitroDataStore)
        assert site['name'] == 'Test'

    def test_getitem_chaining(self):
        """Test chaining __getitem__ calls."""
        data = NitroDataStore({'site': {'config': {'theme': 'dark'}}})
        assert data['site']['config']['theme'] == 'dark'

    def test_setitem(self):
        """Test __setitem__ (data['key'] = value)."""
        data = NitroDataStore()
        data['name'] = 'Test'
        assert data['name'] == 'Test'

    def test_setitem_overwrites(self):
        """Test __setitem__ overwrites existing values."""
        data = NitroDataStore({'name': 'Old'})
        data['name'] = 'New'
        assert data['name'] == 'New'

    def test_delitem(self):
        """Test __delitem__ (del data['key'])."""
        data = NitroDataStore({'name': 'Test', 'other': 'value'})
        del data['name']
        assert 'name' not in data
        assert data['other'] == 'value'

    def test_delitem_missing_raises_keyerror(self):
        """Test __delitem__ with missing key raises KeyError."""
        data = NitroDataStore({'name': 'Test'})
        with pytest.raises(KeyError):
            del data['missing']

    def test_contains(self):
        """Test __contains__ ('key' in data)."""
        data = NitroDataStore({'name': 'Test', 'count': 42})
        assert 'name' in data
        assert 'count' in data
        assert 'missing' not in data


class TestNitroDataStoreDotAccess:
    """Test dot notation access."""

    def test_getattr(self):
        """Test __getattr__ (data.key)."""
        data = NitroDataStore({'name': 'Test', 'count': 42})
        assert data.name == 'Test'
        assert data.count == 42

    def test_getattr_missing_raises_attributeerror(self):
        """Test __getattr__ with missing key raises AttributeError."""
        data = NitroDataStore({'name': 'Test'})
        with pytest.raises(AttributeError):
            _ = data.missing

    def test_getattr_returns_wrapped_dict(self):
        """Test __getattr__ wraps nested dicts in NitroDataStore."""
        data = NitroDataStore({'site': {'name': 'Test'}})
        site = data.site
        assert isinstance(site, NitroDataStore)
        assert site.name == 'Test'

    def test_getattr_chaining(self):
        """Test chaining __getattr__ calls."""
        data = NitroDataStore({'site': {'config': {'theme': 'dark'}}})
        assert data.site.config.theme == 'dark'

    def test_getattr_private_attributes(self):
        """Test that private attributes work normally."""
        data = NitroDataStore({'name': 'Test'})
        # _data should work
        assert isinstance(data._data, dict)

    def test_setattr(self):
        """Test __setattr__ (data.key = value)."""
        data = NitroDataStore()
        data.name = 'Test'
        assert data.name == 'Test'

    def test_setattr_overwrites(self):
        """Test __setattr__ overwrites existing values."""
        data = NitroDataStore({'name': 'Old'})
        data.name = 'New'
        assert data.name == 'New'

    def test_setattr_private_attributes(self):
        """Test that private attributes can be set normally."""
        data = NitroDataStore()
        data._custom = 'value'
        assert data._custom == 'value'


class TestNitroDataStoreMagicMethods:
    """Test other magic methods."""

    def test_len(self):
        """Test __len__ (len(data))."""
        data = NitroDataStore({'a': 1, 'b': 2, 'c': 3})
        assert len(data) == 3

    def test_len_empty(self):
        """Test __len__ with empty datastore."""
        data = NitroDataStore()
        assert len(data) == 0

    def test_len_nested_counts_top_level_only(self):
        """Test that __len__ only counts top-level keys."""
        data = NitroDataStore({
            'site': {'name': 'Test', 'url': 'example.com'},
            'config': {'theme': 'dark'}
        })
        assert len(data) == 2  # Only 'site' and 'config'

    def test_repr(self):
        """Test __repr__."""
        data = NitroDataStore({'name': 'Test'})
        repr_str = repr(data)
        assert 'NitroDataStore' in repr_str
        assert 'name' in repr_str
        assert 'Test' in repr_str

    def test_str(self):
        """Test __str__."""
        data = NitroDataStore({'name': 'Test', 'count': 42})
        str_output = str(data)
        # Should be valid JSON
        parsed = json.loads(str_output)
        assert parsed == {'name': 'Test', 'count': 42}

    def test_str_formatted(self):
        """Test __str__ produces formatted JSON."""
        data = NitroDataStore({'site': {'name': 'Test'}})
        str_output = str(data)
        # Should have newlines (formatted)
        assert '\n' in str_output


class TestNitroDataStoreEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_datastore(self):
        """Test operations on empty datastore."""
        data = NitroDataStore()
        assert len(data) == 0
        assert data.get('any.key') is None
        assert data.has('any.key') is False
        assert data.to_dict() == {}

    def test_mixed_access_patterns(self):
        """Test mixing different access patterns."""
        data = NitroDataStore()

        # Set with dot notation
        data.set('site.name', 'Test')

        # Access with dict notation
        assert data['site']['name'] == 'Test'

        # Access with dot notation
        assert data.site.name == 'Test'

        # Access with get
        assert data.get('site.name') == 'Test'

    def test_modifying_returned_datastore(self):
        """Test that modifying returned NitroDataStore affects original."""
        data = NitroDataStore({'site': {'name': 'Old'}})

        # Get nested datastore
        site = data.site
        site.name = 'New'

        # Original should be modified
        assert data.get('site.name') == 'New'

    def test_to_dict_is_deep_copy(self):
        """Test that to_dict returns a deep copy."""
        data = NitroDataStore({'site': {'name': 'Test'}})
        exported = data.to_dict()

        # Modify the exported dict
        exported['site']['name'] = 'Modified'

        # Original should be unchanged
        assert data.get('site.name') == 'Test'

    def test_nested_lists_preserved(self):
        """Test that nested lists are preserved correctly."""
        data = NitroDataStore({
            'tags': ['python', 'web', 'cli'],
            'nested': {
                'items': [1, 2, 3]
            }
        })

        assert data.get('tags') == ['python', 'web', 'cli']
        assert data.get('nested.items') == [1, 2, 3]
        assert data.tags == ['python', 'web', 'cli']

    def test_unicode_support(self):
        """Test Unicode character support."""
        data = NitroDataStore({
            'japanese': '日本語',
            'emoji': '🚀',
            'chinese': '中文'
        })

        assert data.get('japanese') == '日本語'
        assert data.get('emoji') == '🚀'
        assert data.get('chinese') == '中文'

    def test_numeric_string_keys(self):
        """Test keys that look like numbers."""
        data = NitroDataStore({'123': 'value', '456': {'789': 'nested'}})
        assert data.get('123') == 'value'
        assert data.get('456.789') == 'nested'

    def test_special_character_keys(self):
        """Test keys with special characters (that aren't dots)."""
        data = NitroDataStore({
            'key-with-dashes': 'value1',
            'key_with_underscores': 'value2',
            'key:with:colons': 'value3'
        })

        # Dict access should work
        assert data['key-with-dashes'] == 'value1'
        assert data['key_with_underscores'] == 'value2'
        assert data['key:with:colons'] == 'value3'

    def test_boolean_and_none_values(self):
        """Test storing boolean and None values."""
        data = NitroDataStore({
            'enabled': True,
            'disabled': False,
            'nullable': None
        })

        assert data.get('enabled') is True
        assert data.get('disabled') is False
        assert data.get('nullable') is None

    def test_deep_merge_with_lists(self):
        """Test that deep merge replaces lists (doesn't merge them)."""
        data1 = NitroDataStore({'tags': ['a', 'b']})
        data2 = NitroDataStore({'tags': ['c', 'd']})

        data1.merge(data2)

        # Lists should be replaced, not merged
        assert data1.get('tags') == ['c', 'd']

    def test_getattr_invalid_private_attribute(self):
        """Test accessing a non-existent private attribute raises AttributeError."""
        data = NitroDataStore({'name': 'Test'})
        with pytest.raises(AttributeError, match="has no attribute '_nonexistent'"):
            _ = data._nonexistent

    def test_to_dict_deep_copies_nested_lists(self):
        """Test that to_dict deep copies nested lists."""
        data = NitroDataStore({
            'items': {
                'list1': [1, 2, 3],
                'list2': ['a', 'b', 'c']
            }
        })
        exported = data.to_dict()

        # Modify the exported lists
        exported['items']['list1'].append(4)
        exported['items']['list2'].append('d')

        # Original should be unchanged
        assert data.get('items.list1') == [1, 2, 3]
        assert data.get('items.list2') == ['a', 'b', 'c']


class TestNitroDataStorePathIntrospection:
    """Test path introspection utilities."""

    def test_list_paths_simple(self):
        """Test listing all paths in simple structure."""
        data = NitroDataStore({'site': {'name': 'Test', 'url': 'example.com'}})
        paths = data.list_paths()
        assert set(paths) == {'site', 'site.name', 'site.url'}

    def test_list_paths_nested(self):
        """Test listing paths in deeply nested structure."""
        data = NitroDataStore({
            'config': {
                'theme': {
                    'colors': {
                        'primary': '#007bff'
                    }
                }
            }
        })
        paths = data.list_paths()
        assert 'config' in paths
        assert 'config.theme' in paths
        assert 'config.theme.colors' in paths
        assert 'config.theme.colors.primary' in paths

    def test_list_paths_with_lists(self):
        """Test listing paths with list indices."""
        data = NitroDataStore({'posts': [{'title': 'A'}, {'title': 'B'}]})
        paths = data.list_paths()
        assert 'posts' in paths
        assert 'posts.0' in paths
        assert 'posts.1' in paths
        assert 'posts.0.title' in paths
        assert 'posts.1.title' in paths

    def test_list_paths_with_prefix(self):
        """Test filtering paths by prefix."""
        data = NitroDataStore({
            'site': {'name': 'Test', 'url': 'example.com'},
            'theme': {'color': 'blue'}
        })
        paths = data.list_paths(prefix='site')
        assert all(p.startswith('site') for p in paths)
        assert 'theme' not in paths

    def test_find_paths_wildcard_single(self):
        """Test finding paths with single wildcard."""
        data = NitroDataStore({'posts': [{'title': 'A'}, {'title': 'B'}]})
        paths = data.find_paths('posts.*.title')
        assert set(paths) == {'posts.0.title', 'posts.1.title'}

    def test_find_paths_wildcard_any(self):
        """Test finding paths with ** wildcard."""
        data = NitroDataStore({
            'a': {'b': {'c': 1}},
            'x': {'y': {'c': 2}}
        })
        paths = data.find_paths('**.c')
        assert 'a.b.c' in paths
        assert 'x.y.c' in paths

    def test_get_many(self):
        """Test getting multiple paths at once."""
        data = NitroDataStore({
            'site': {'name': 'Test', 'url': 'example.com'},
            'theme': 'dark'
        })
        result = data.get_many(['site.name', 'site.url', 'theme', 'missing'])
        assert result == {
            'site.name': 'Test',
            'site.url': 'example.com',
            'theme': 'dark',
            'missing': None
        }


class TestNitroDataStoreDeepSearch:
    """Test deep search utilities."""

    def test_find_all_keys(self):
        """Test finding all occurrences of a key name."""
        data = NitroDataStore({
            'site': {'url': 'site.com'},
            'social': {'github': {'url': 'github.com'}}
        })
        result = data.find_all_keys('url')
        assert result == {
            'site.url': 'site.com',
            'social.github.url': 'github.com'
        }

    def test_find_all_keys_single_occurrence(self):
        """Test finding key with single occurrence."""
        data = NitroDataStore({'name': 'Test', 'info': {'age': 25}})
        result = data.find_all_keys('name')
        assert result == {'name': 'Test'}

    def test_find_all_keys_no_matches(self):
        """Test finding key that doesn't exist."""
        data = NitroDataStore({'name': 'Test'})
        result = data.find_all_keys('missing')
        assert result == {}

    def test_find_values_by_type(self):
        """Test finding values by type."""
        data = NitroDataStore({
            'name': 'test',
            'count': 42,
            'enabled': True,
            'nested': {'value': 'hello'}
        })
        result = data.find_values(lambda v: isinstance(v, str))
        assert set(result.keys()) == {'name', 'nested.value'}

    def test_find_values_by_pattern(self):
        """Test finding values matching pattern."""
        data = NitroDataStore({
            'images': {'hero': 'pic.jpg', 'thumb': 'small.png'},
            'count': 5
        })
        result = data.find_values(lambda v: isinstance(v, str) and v.endswith('.jpg'))
        assert result == {'images.hero': 'pic.jpg'}


class TestNitroDataStoreBulkOperations:
    """Test bulk operations."""

    def test_update_where(self):
        """Test updating values matching condition."""
        data = NitroDataStore({
            'urls': ['http://a.com', 'https://b.com', 'http://c.com']
        })
        count = data.update_where(
            lambda p, v: isinstance(v, str) and 'http://' in v,
            lambda v: v.replace('http://', 'https://')
        )
        assert count == 2
        assert all('https://' in url for url in data.urls)

    def test_update_where_nested(self):
        """Test updating nested values."""
        data = NitroDataStore({
            'site': {'url': 'http://site.com'},
            'social': {'github': 'http://github.com'}
        })
        count = data.update_where(
            lambda p, v: isinstance(v, str) and 'http://' in v,
            lambda v: v.replace('http://', 'https://')
        )
        assert count == 2
        assert data.get('site.url') == 'https://site.com'
        assert data.get('social.github') == 'https://github.com'

    def test_remove_nulls(self):
        """Test removing None values."""
        data = NitroDataStore({
            'a': 1,
            'b': None,
            'c': {'d': None, 'e': 2}
        })
        count = data.remove_nulls()
        assert count == 2
        assert data.to_dict() == {'a': 1, 'c': {'e': 2}}

    def test_remove_nulls_in_lists(self):
        """Test removing None from lists."""
        data = NitroDataStore({'items': [1, None, 2, None, 3]})
        count = data.remove_nulls()
        assert count == 2
        assert data['items'] == [1, 2, 3]

    def test_remove_empty(self):
        """Test removing empty containers."""
        data = NitroDataStore({
            'a': {},
            'b': [],
            'c': {'d': 1, 'e': {}},
            'f': 'value'
        })
        count = data.remove_empty()
        assert count == 3  # 'a', 'b', and 'c.e'
        result = data.to_dict()
        assert 'a' not in result
        assert 'b' not in result
        assert result['c'] == {'d': 1}

    def test_remove_empty_nested_lists(self):
        """Test removing empty nested lists."""
        data = NitroDataStore({'items': [[], [1], []]})
        count = data.remove_empty()
        assert count == 2
        assert data['items'] == [[1]]


class TestNitroDataStoreIntrospection:
    """Test data introspection."""

    def test_describe_simple(self):
        """Test describing simple structure."""
        data = NitroDataStore({'name': 'Test', 'count': 42})
        description = data.describe()
        assert description['name']['type'] == 'str'
        assert description['count']['type'] == 'int'

    def test_describe_nested(self):
        """Test describing nested structure."""
        data = NitroDataStore({
            'site': {
                'name': 'Test',
                'settings': {'theme': 'dark'}
            }
        })
        description = data.describe()
        assert description['site']['type'] == 'dict'
        assert 'name' in description['site']['structure']

    def test_describe_list(self):
        """Test describing lists."""
        data = NitroDataStore({'posts': [{'title': 'A'}, {'title': 'B'}]})
        description = data.describe()
        assert description['posts']['type'] == 'list'
        assert description['posts']['length'] == 2
        assert 'dict' in description['posts']['item_types']

    def test_stats(self):
        """Test getting statistics."""
        data = NitroDataStore({
            'a': {'b': {'c': 1}},
            'x': [1, 2, 3]
        })
        stats = data.stats()
        assert stats['total_dicts'] == 3  # root + a + b
        assert stats['total_lists'] == 1  # x
        assert stats['total_keys'] == 4  # root has keys: a, x; a has key: b; b has key: c
        assert stats['max_depth'] >= 2

    def test_stats_empty(self):
        """Test stats on empty datastore."""
        data = NitroDataStore()
        stats = data.stats()
        assert stats['total_dicts'] == 1  # root dict
        assert stats['total_lists'] == 0
        assert stats['total_keys'] == 0


class TestNitroDataStoreQueryBuilder:
    """Test query builder."""

    def test_query_where(self):
        """Test basic where filtering."""
        data = NitroDataStore({
            'posts': [
                {'title': 'A', 'published': True},
                {'title': 'B', 'published': False},
                {'title': 'C', 'published': True}
            ]
        })
        results = data.query('posts').where(lambda x: x.get('published')).execute()
        assert len(results) == 2
        assert all(p['published'] for p in results)

    def test_query_sort(self):
        """Test sorting results."""
        data = NitroDataStore({
            'posts': [
                {'title': 'C', 'order': 3},
                {'title': 'A', 'order': 1},
                {'title': 'B', 'order': 2}
            ]
        })
        results = data.query('posts').sort(key=lambda x: x.get('order')).execute()
        assert results[0]['title'] == 'A'
        assert results[1]['title'] == 'B'
        assert results[2]['title'] == 'C'

    def test_query_sort_reverse(self):
        """Test reverse sorting."""
        data = NitroDataStore({
            'posts': [
                {'title': 'A', 'views': 100},
                {'title': 'B', 'views': 300},
                {'title': 'C', 'views': 200}
            ]
        })
        results = data.query('posts').sort(key=lambda x: x.get('views'), reverse=True).execute()
        assert results[0]['title'] == 'B'  # 300 views

    def test_query_limit(self):
        """Test limiting results."""
        data = NitroDataStore({'posts': [{'n': i} for i in range(10)]})
        results = data.query('posts').limit(3).execute()
        assert len(results) == 3

    def test_query_offset(self):
        """Test offsetting results."""
        data = NitroDataStore({'posts': [{'n': i} for i in range(10)]})
        results = data.query('posts').offset(5).execute()
        assert len(results) == 5
        assert results[0]['n'] == 5

    def test_query_chaining(self):
        """Test chaining multiple operations."""
        data = NitroDataStore({
            'posts': [
                {'title': 'A', 'published': True, 'views': 100},
                {'title': 'B', 'published': False, 'views': 300},
                {'title': 'C', 'published': True, 'views': 200},
                {'title': 'D', 'published': True, 'views': 150}
            ]
        })
        results = (data.query('posts')
                   .where(lambda x: x.get('published'))
                   .sort(key=lambda x: x.get('views'), reverse=True)
                   .limit(2)
                   .execute())
        assert len(results) == 2
        assert results[0]['title'] == 'C'  # 200 views
        assert results[1]['title'] == 'D'  # 150 views

    def test_query_count(self):
        """Test counting results."""
        data = NitroDataStore({
            'posts': [
                {'published': True},
                {'published': False},
                {'published': True}
            ]
        })
        count = data.query('posts').where(lambda x: x.get('published')).count()
        assert count == 2

    def test_query_first(self):
        """Test getting first result."""
        data = NitroDataStore({
            'posts': [{'title': 'A'}, {'title': 'B'}]
        })
        first = data.query('posts').first()
        assert first == {'title': 'A'}

    def test_query_first_none(self):
        """Test first on empty results."""
        data = NitroDataStore({'posts': []})
        first = data.query('posts').first()
        assert first is None

    def test_query_pluck(self):
        """Test plucking field values."""
        data = NitroDataStore({
            'posts': [
                {'title': 'A', 'views': 100},
                {'title': 'B', 'views': 200}
            ]
        })
        titles = data.query('posts').pluck('title')
        assert titles == ['A', 'B']

    def test_query_group_by(self):
        """Test grouping results."""
        data = NitroDataStore({
            'posts': [
                {'title': 'A', 'category': 'python'},
                {'title': 'B', 'category': 'web'},
                {'title': 'C', 'category': 'python'}
            ]
        })
        groups = data.query('posts').group_by('category')
        assert len(groups['python']) == 2
        assert len(groups['web']) == 1


class TestNitroDataStoreTransformations:
    """Test transformation utilities."""

    def test_transform_all(self):
        """Test transforming all values."""
        data = NitroDataStore({'name': 'test', 'title': 'hello'})
        upper = data.transform_all(lambda p, v: v.upper() if isinstance(v, str) else v)
        assert upper.name == 'TEST'
        assert upper.title == 'HELLO'
        # Original unchanged
        assert data.name == 'test'

    def test_transform_all_nested(self):
        """Test transforming nested values."""
        data = NitroDataStore({
            'site': {'name': 'test', 'count': 5}
        })
        transformed = data.transform_all(lambda p, v: v.upper() if isinstance(v, str) else v)
        assert transformed.site.name == 'TEST'
        assert transformed.site.count == 5

    def test_transform_keys(self):
        """Test transforming keys."""
        data = NitroDataStore({
            'first-name': 'John',
            'last-name': 'Doe'
        })
        snake = data.transform_keys(lambda k: k.replace('-', '_'))
        assert 'first_name' in snake
        assert 'last_name' in snake
        # Original unchanged
        assert 'first-name' in data

    def test_transform_keys_nested(self):
        """Test transforming nested keys."""
        data = NitroDataStore({
            'user-info': {
                'first-name': 'John'
            }
        })
        snake = data.transform_keys(lambda k: k.replace('-', '_'))
        assert 'user_info' in snake
        assert snake.get('user_info.first_name') == 'John'


class TestNitroDataStoreDiff:
    """Test diff and equals."""

    def test_diff_added(self):
        """Test detecting added keys."""
        data1 = NitroDataStore({'a': 1})
        data2 = NitroDataStore({'a': 1, 'b': 2})
        diff = data1.diff(data2)
        assert diff['added'] == {'b': 2}
        assert diff['removed'] == {}
        assert diff['changed'] == {}

    def test_diff_removed(self):
        """Test detecting removed keys."""
        data1 = NitroDataStore({'a': 1, 'b': 2})
        data2 = NitroDataStore({'a': 1})
        diff = data1.diff(data2)
        assert diff['removed'] == {'b': 2}
        assert diff['added'] == {}

    def test_diff_changed(self):
        """Test detecting changed values."""
        data1 = NitroDataStore({'a': 1, 'b': 2})
        data2 = NitroDataStore({'a': 1, 'b': 3})
        diff = data1.diff(data2)
        assert diff['changed'] == {'b': {'old': 2, 'new': 3}}

    def test_diff_complex(self):
        """Test diff with complex changes."""
        data1 = NitroDataStore({
            'site': {'name': 'Old', 'url': 'old.com'},
            'theme': 'light'
        })
        data2 = NitroDataStore({
            'site': {'name': 'New', 'url': 'old.com'},
            'version': '2.0'
        })
        diff = data1.diff(data2)
        assert 'site.name' in diff['changed']
        assert 'version' in diff['added']
        assert 'theme' in diff['removed']

    def test_equals_true(self):
        """Test equals with identical data."""
        data1 = NitroDataStore({'a': 1, 'b': {'c': 2}})
        data2 = NitroDataStore({'a': 1, 'b': {'c': 2}})
        assert data1.equals(data2)

    def test_equals_false(self):
        """Test equals with different data."""
        data1 = NitroDataStore({'a': 1})
        data2 = NitroDataStore({'a': 2})
        assert not data1.equals(data2)

    def test_equals_with_dict(self):
        """Test equals with plain dict."""
        data = NitroDataStore({'a': 1})
        assert data.equals({'a': 1})
        assert not data.equals({'a': 2})


class TestNitroDataStoreFilterList:
    """Test filter_list utility."""

    def test_filter_list(self):
        """Test filtering a list."""
        data = NitroDataStore({
            'posts': [
                {'title': 'A', 'published': True},
                {'title': 'B', 'published': False},
                {'title': 'C', 'published': True}
            ]
        })
        published = data.filter_list('posts', lambda p: p.get('published'))
        assert len(published) == 2
        assert all(p['published'] for p in published)

    def test_filter_list_not_list(self):
        """Test filter_list on non-list returns empty."""
        data = NitroDataStore({'value': 'not a list'})
        result = data.filter_list('value', lambda x: True)
        assert result == []

    def test_filter_list_missing_path(self):
        """Test filter_list on missing path returns empty."""
        data = NitroDataStore({'other': 'value'})
        result = data.filter_list('missing', lambda x: True)
        assert result == []