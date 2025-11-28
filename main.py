#!/usr/bin/env python3
"""Test script for nitro-cli integration with external packages."""

def test_imports():
    """Test that all external package imports work correctly."""
    print("Testing imports...")

    # Test nitro-ui import
    try:
        from nitro_ui import HTML, Head, Body, Div, H1, Paragraph
        print("  ✓ nitro-ui imported successfully")
    except ImportError as e:
        print(f"  ✗ nitro-ui import failed: {e}")
        return False

    # Test nitro-datastore import
    try:
        from nitro_datastore import NitroDataStore
        print("  ✓ nitro-datastore imported successfully")
    except ImportError as e:
        print(f"  ✗ nitro-datastore import failed: {e}")
        return False

    # Test nitro-dispatch import
    try:
        from nitro_dispatch import PluginManager, PluginBase, hook
        print("  ✓ nitro-dispatch imported successfully")
    except ImportError as e:
        print(f"  ✗ nitro-dispatch import failed: {e}")
        return False

    # Test nitro package imports
    try:
        from nitro import Config, Page, load_data
        print("  ✓ nitro package imports successful")
    except ImportError as e:
        print(f"  ✗ nitro package import failed: {e}")
        return False

    # Test plugin system imports
    try:
        from nitro.plugins import NitroPlugin, PluginLoader, hook
        print("  ✓ nitro.plugins imports successful")
    except ImportError as e:
        print(f"  ✗ nitro.plugins import failed: {e}")
        return False

    return True


def test_nitro_ui():
    """Test nitro-ui HTML generation."""
    print("\nTesting nitro-ui...")

    from nitro_ui import HTML, Head, Body, Title, Div, H1, Paragraph

    page = HTML(
        Head(Title("Test Page")),
        Body(
            Div(
                H1("Hello World"),
                Paragraph("This is a test page generated with nitro-ui."),
            )
        )
    )

    html = page.render()
    assert "<h1>Hello World</h1>" in html
    assert "<title>Test Page</title>" in html
    print("  ✓ nitro-ui HTML generation works correctly")
    return True


def test_datastore():
    """Test nitro-datastore functionality."""
    print("\nTesting nitro-datastore...")

    from nitro_datastore import NitroDataStore

    # Test creating a datastore from dict
    data = NitroDataStore({
        "site": {
            "name": "Test Site",
            "description": "A test site"
        },
        "features": ["feature1", "feature2"]
    })

    # Test dot notation access
    assert data.site.name == "Test Site"
    print("  ✓ Dot notation access works")

    # Test path-based access
    assert data.get("site.description") == "A test site"
    print("  ✓ Path-based access works")

    return True


def test_dispatch():
    """Test nitro-dispatch plugin system."""
    print("\nTesting nitro-dispatch...")

    from nitro_dispatch import PluginManager, PluginBase, hook

    class TestPlugin(PluginBase):
        name = "test-plugin"
        version = "1.0.0"

        @hook("test.event", priority=100)
        def handle_event(self, data):
            data["processed"] = True
            return data

    manager = PluginManager()
    manager.register(TestPlugin)
    manager.load_all()

    result = manager.trigger("test.event", {"value": 42})
    assert result.get("processed") == True
    print("  ✓ Plugin hook system works")

    return True


if __name__ == "__main__":
    print("=" * 50)
    print("Nitro CLI Integration Test")
    print("=" * 50)

    all_passed = True

    if not test_imports():
        all_passed = False
        print("\n⚠️  Install packages first: pip install nitro-ui nitro-datastore nitro-dispatch")
    else:
        try:
            test_nitro_ui()
        except Exception as e:
            print(f"  ✗ nitro-ui test failed: {e}")
            all_passed = False

        try:
            test_datastore()
        except Exception as e:
            print(f"  ✗ nitro-datastore test failed: {e}")
            all_passed = False

        try:
            test_dispatch()
        except Exception as e:
            print(f"  ✗ nitro-dispatch test failed: {e}")
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("All tests passed! ✓")
    else:
        print("Some tests failed. See above for details.")
    print("=" * 50)
