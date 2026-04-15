"""Tests for core/cache.py."""

import json
import tempfile
from pathlib import Path

import pytest

from nitro.core.cache import BuildCache


class TestBuildCacheInit:
    """Tests for BuildCache initialization."""

    def test_empty_cache_when_no_file(self):
        """Should initialise with an empty cache when no cache file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = BuildCache(Path(tmpdir))

            assert cache._cache["version"] == BuildCache.CACHE_VERSION
            assert cache._cache["pages"] == {}
            assert cache._cache["components"] == {}
            assert cache._cache["data"] == {}
            assert cache._cache["config_hash"] is None
            assert cache._cache["last_build"] is None

    def test_loads_existing_valid_cache(self):
        """Should load and use a valid cache file that exists on disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            cache_dir = project_root / ".nitro"
            cache_dir.mkdir()
            cache_file = cache_dir / "cache.json"
            existing = {
                "version": BuildCache.CACHE_VERSION,
                "pages": {"src/pages/index.py": {"hash": "abc123", "built_at": "2026-01-01T00:00:00"}},
                "components": {},
                "data": {},
                "config_hash": "def456",
                "last_build": "2026-01-01T00:00:00",
            }
            cache_file.write_text(json.dumps(existing))

            cache = BuildCache(project_root)

            assert cache._cache["pages"]["src/pages/index.py"]["hash"] == "abc123"
            assert cache._cache["config_hash"] == "def456"

    def test_resets_cache_on_wrong_version(self):
        """Should discard an existing cache whose version does not match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            cache_dir = project_root / ".nitro"
            cache_dir.mkdir()
            cache_file = cache_dir / "cache.json"
            stale = {
                "version": 999,
                "pages": {"src/pages/index.py": {"hash": "oldvalue"}},
                "components": {},
                "data": {},
                "config_hash": "stale",
                "last_build": None,
            }
            cache_file.write_text(json.dumps(stale))

            cache = BuildCache(project_root)

            assert cache._cache["pages"] == {}
            assert cache._cache["config_hash"] is None
            assert cache._cache["version"] == BuildCache.CACHE_VERSION

    def test_resets_cache_on_corrupted_json(self):
        """Should fall back to an empty cache when the JSON on disk is corrupt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            cache_dir = project_root / ".nitro"
            cache_dir.mkdir()
            (cache_dir / "cache.json").write_text("{ this is not valid json !!!")

            cache = BuildCache(project_root)

            assert cache._cache["pages"] == {}
            assert cache._cache["version"] == BuildCache.CACHE_VERSION

    def test_sets_correct_paths(self):
        """project_root, cache_path, and cache_dir should be derived correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            cache = BuildCache(project_root)

            assert cache.project_root == project_root
            assert cache.cache_path == project_root / ".nitro" / "cache.json"
            assert cache.cache_dir == project_root / ".nitro"


class TestBuildCacheSave:
    """Tests for BuildCache.save()."""

    def test_save_creates_nitro_directory(self):
        """save() should create the .nitro directory when it does not exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            cache = BuildCache(project_root)

            assert not (project_root / ".nitro").exists()
            cache.save()

            assert (project_root / ".nitro").is_dir()

    def test_save_writes_json_file(self):
        """save() should write a valid JSON file at the expected path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            cache = BuildCache(project_root)
            cache.save()

            cache_file = project_root / ".nitro" / "cache.json"
            assert cache_file.exists()

            data = json.loads(cache_file.read_text())
            assert data["version"] == BuildCache.CACHE_VERSION

    def test_save_sets_last_build_timestamp(self):
        """save() should record a last_build ISO timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            cache = BuildCache(project_root)
            cache.save()

            data = json.loads((project_root / ".nitro" / "cache.json").read_text())
            assert data["last_build"] is not None
            # Should be a non-empty ISO 8601 string
            assert "T" in data["last_build"]

    def test_save_then_reload_preserves_data(self):
        """Data stored before save() should be loadable by a new BuildCache instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            cache = BuildCache(project_root)
            cache._cache["config_hash"] = "persist_me"
            cache.save()

            reloaded = BuildCache(project_root)
            assert reloaded._cache["config_hash"] == "persist_me"

    def test_save_is_idempotent(self):
        """Calling save() twice should not raise and the file should remain valid."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            cache = BuildCache(project_root)
            cache.save()
            cache.save()

            data = json.loads((project_root / ".nitro" / "cache.json").read_text())
            assert data["version"] == BuildCache.CACHE_VERSION


class TestIsConfigChanged:
    """Tests for BuildCache.is_config_changed() and update_config_hash()."""

    def test_config_changed_when_cache_empty(self):
        """Any existing config file should appear changed against an empty cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config_path = project_root / "nitro.config.py"
            config_path.write_text("config = None")

            cache = BuildCache(project_root)

            assert cache.is_config_changed(config_path) is True

    def test_config_unchanged_after_update(self):
        """After update_config_hash(), is_config_changed() should return False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config_path = project_root / "nitro.config.py"
            config_path.write_text("config = None")

            cache = BuildCache(project_root)
            cache.update_config_hash(config_path)

            assert cache.is_config_changed(config_path) is False

    def test_config_changed_after_content_modification(self):
        """Modifying the config file should cause is_config_changed() to return True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config_path = project_root / "nitro.config.py"
            config_path.write_text("config = None")

            cache = BuildCache(project_root)
            cache.update_config_hash(config_path)

            # Mutate the file
            config_path.write_text("config = None  # changed")

            assert cache.is_config_changed(config_path) is True

    def test_config_changed_when_file_missing(self):
        """A missing config file should report as changed (hash is None vs stored)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config_path = project_root / "nitro.config.py"
            config_path.write_text("config = None")

            cache = BuildCache(project_root)
            cache.update_config_hash(config_path)

            config_path.unlink()

            assert cache.is_config_changed(config_path) is True

    def test_update_config_hash_stores_hash(self):
        """update_config_hash() should write the file's hash into the cache dict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config_path = project_root / "nitro.config.py"
            config_path.write_text("config = None")

            cache = BuildCache(project_root)
            cache.update_config_hash(config_path)

            assert cache._cache["config_hash"] is not None
            assert len(cache._cache["config_hash"]) == 16  # truncated SHA256


class TestGetChangedPages:
    """Tests for BuildCache.get_changed_pages()."""

    def _make_page(self, pages_dir: Path, name: str, content: str = "render = None") -> Path:
        path = pages_dir / name
        path.write_text(content)
        return path

    def test_all_pages_changed_on_empty_cache(self):
        """All pages should appear as changed when the cache is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)

            pages = [
                self._make_page(pages_dir, "index.py"),
                self._make_page(pages_dir, "about.py"),
            ]
            components_dir = project_root / "src" / "components"
            data_dir = project_root / "src" / "data"

            cache = BuildCache(project_root)
            changed = cache.get_changed_pages(pages, components_dir, data_dir)

            assert set(changed) == set(pages)

    def test_unchanged_pages_not_returned(self):
        """Pages whose hash matches the cache should not be returned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)
            components_dir = project_root / "src" / "components"
            data_dir = project_root / "src" / "data"

            page = self._make_page(pages_dir, "index.py")
            cache = BuildCache(project_root)

            # Record the page as already built
            cache.update_page_hash(page)

            changed = cache.get_changed_pages([page], components_dir, data_dir)

            assert changed == []

    def test_modified_page_detected(self):
        """A page whose content changed since the last build should be returned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)
            components_dir = project_root / "src" / "components"
            data_dir = project_root / "src" / "data"

            page = self._make_page(pages_dir, "index.py", "v1 = True")
            cache = BuildCache(project_root)
            cache.update_page_hash(page)

            # Simulate an edit
            page.write_text("v2 = True")

            changed = cache.get_changed_pages([page], components_dir, data_dir)

            assert page in changed

    def test_component_change_triggers_all_pages(self):
        """When a component changes, every page must be rebuilt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)
            components_dir = project_root / "src" / "components"
            components_dir.mkdir(parents=True)
            data_dir = project_root / "src" / "data"

            page1 = self._make_page(pages_dir, "index.py")
            page2 = self._make_page(pages_dir, "about.py")

            component = components_dir / "header.py"
            component.write_text("def header(): pass")

            cache = BuildCache(project_root)

            # Mark pages and component as already known
            cache.update_page_hash(page1)
            cache.update_page_hash(page2)
            # Seed the component hashes so a first call does not auto-flag as new
            cache._update_component_hashes(components_dir)

            # Modify the component
            component.write_text("def header(): return 'changed'")

            changed = cache.get_changed_pages([page1, page2], components_dir, data_dir)

            assert page1 in changed
            assert page2 in changed

    def test_data_change_triggers_all_pages(self):
        """When a data file changes, every page must be rebuilt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)
            components_dir = project_root / "src" / "components"
            data_dir = project_root / "src" / "data"
            data_dir.mkdir(parents=True)

            page1 = self._make_page(pages_dir, "index.py")
            page2 = self._make_page(pages_dir, "blog.py")

            data_file = data_dir / "posts.json"
            data_file.write_text('{"posts": []}')

            cache = BuildCache(project_root)
            cache.update_page_hash(page1)
            cache.update_page_hash(page2)
            # Seed data hashes
            cache._update_data_hashes(data_dir)

            # Modify the data file
            data_file.write_text('{"posts": [{"title": "New"}]}')

            changed = cache.get_changed_pages([page1, page2], components_dir, data_dir)

            assert page1 in changed
            assert page2 in changed

    def test_no_changes_returns_empty_list(self):
        """Returns an empty list when no pages, components, or data have changed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)
            components_dir = project_root / "src" / "components"
            components_dir.mkdir(parents=True)
            data_dir = project_root / "src" / "data"
            data_dir.mkdir(parents=True)

            component = components_dir / "nav.py"
            component.write_text("def nav(): pass")

            data_file = data_dir / "site.yaml"
            data_file.write_text("title: My Site")

            page = self._make_page(pages_dir, "index.py")

            cache = BuildCache(project_root)
            cache.update_page_hash(page)
            # Seed component and data hashes so nothing appears new
            cache._update_component_hashes(components_dir)
            cache._update_data_hashes(data_dir)

            changed = cache.get_changed_pages([page], components_dir, data_dir)

            assert changed == []

    def test_missing_components_dir_does_not_raise(self):
        """get_changed_pages() should work normally when components_dir is absent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)
            components_dir = project_root / "src" / "components"  # does not exist
            data_dir = project_root / "src" / "data"  # does not exist

            page = self._make_page(pages_dir, "index.py")
            cache = BuildCache(project_root)
            cache.update_page_hash(page)

            changed = cache.get_changed_pages([page], components_dir, data_dir)

            assert changed == []

    def test_deleted_component_triggers_all_pages(self):
        """Removing a component file should flag all pages for rebuild."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)
            components_dir = project_root / "src" / "components"
            components_dir.mkdir(parents=True)
            data_dir = project_root / "src" / "data"

            component = components_dir / "footer.py"
            component.write_text("def footer(): pass")

            page = self._make_page(pages_dir, "index.py")

            cache = BuildCache(project_root)
            cache.update_page_hash(page)
            cache._update_component_hashes(components_dir)

            # Remove the component
            component.unlink()

            changed = cache.get_changed_pages([page], components_dir, data_dir)

            assert page in changed

    def test_deleted_data_file_triggers_all_pages(self):
        """Removing a data file should flag all pages for rebuild."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)
            components_dir = project_root / "src" / "components"
            data_dir = project_root / "src" / "data"
            data_dir.mkdir(parents=True)

            data_file = data_dir / "config.yml"
            data_file.write_text("key: value")

            page = self._make_page(pages_dir, "index.py")

            cache = BuildCache(project_root)
            cache.update_page_hash(page)
            cache._update_data_hashes(data_dir)

            data_file.unlink()

            changed = cache.get_changed_pages([page], components_dir, data_dir)

            assert page in changed

    def test_init_py_in_components_ignored(self):
        """__init__.py files inside components_dir should not affect change detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)
            components_dir = project_root / "src" / "components"
            components_dir.mkdir(parents=True)
            data_dir = project_root / "src" / "data"

            # Only an __init__.py present – should be ignored entirely
            (components_dir / "__init__.py").write_text("")

            page = self._make_page(pages_dir, "index.py")
            cache = BuildCache(project_root)
            cache.update_page_hash(page)
            # Seed with the __init__.py present (it is ignored, so hashes stay empty)
            cache._update_component_hashes(components_dir)

            # Modify __init__.py – should not trigger a rebuild
            (components_dir / "__init__.py").write_text("# modified")

            changed = cache.get_changed_pages([page], components_dir, data_dir)

            assert changed == []

    def test_non_data_extension_files_ignored(self):
        """Files without .json/.yaml/.yml extension in data_dir should be ignored."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)
            components_dir = project_root / "src" / "components"
            data_dir = project_root / "src" / "data"
            data_dir.mkdir(parents=True)

            (data_dir / "readme.txt").write_text("docs")
            (data_dir / "script.py").write_text("x = 1")

            page = self._make_page(pages_dir, "index.py")
            cache = BuildCache(project_root)
            cache.update_page_hash(page)
            cache._update_data_hashes(data_dir)

            # Modify ignored files
            (data_dir / "readme.txt").write_text("docs updated")

            changed = cache.get_changed_pages([page], components_dir, data_dir)

            assert changed == []


class TestUpdatePageHash:
    """Tests for BuildCache.update_page_hash()."""

    def test_stores_hash_and_built_at(self):
        """update_page_hash() should record hash and built_at for the page."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)

            page = pages_dir / "index.py"
            page.write_text("render = None")

            cache = BuildCache(project_root)
            cache.update_page_hash(page)

            rel_path = str(page.relative_to(project_root))
            entry = cache._cache["pages"][rel_path]

            assert entry["hash"] is not None
            assert len(entry["hash"]) == 16
            assert "built_at" in entry
            assert "T" in entry["built_at"]

    def test_hash_changes_with_file_content(self):
        """The stored hash should differ when the file content differs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)

            page = pages_dir / "index.py"
            page.write_text("version = 1")

            cache = BuildCache(project_root)
            cache.update_page_hash(page)
            rel_path = str(page.relative_to(project_root))
            hash_v1 = cache._cache["pages"][rel_path]["hash"]

            page.write_text("version = 2")
            cache.update_page_hash(page)
            hash_v2 = cache._cache["pages"][rel_path]["hash"]

            assert hash_v1 != hash_v2

    def test_page_outside_project_root_uses_absolute_path(self):
        """A page path that cannot be made relative should be stored as its absolute path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "project"
            project_root.mkdir()

            # Page lives outside project_root
            with tempfile.TemporaryDirectory() as other:
                external_page = Path(other) / "external.py"
                external_page.write_text("render = None")

                cache = BuildCache(project_root)
                cache.update_page_hash(external_page)

                # Key should be the absolute path string, not a relative one
                assert str(external_page) in cache._cache["pages"]

    def test_update_page_hash_persists_across_save_reload(self):
        """A page hash saved to disk should be present after reloading the cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pages_dir = project_root / "src" / "pages"
            pages_dir.mkdir(parents=True)

            page = pages_dir / "index.py"
            page.write_text("render = None")

            cache = BuildCache(project_root)
            cache.update_page_hash(page)
            cache.save()

            reloaded = BuildCache(project_root)
            rel_path = str(page.relative_to(project_root))
            assert rel_path in reloaded._cache["pages"]
            assert reloaded._cache["pages"][rel_path]["hash"] is not None
