"""Tests for core/islands.py."""

import hashlib
import json
from unittest.mock import patch

import pytest

from nitro.core.islands import Island, IslandConfig, IslandProcessor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _expected_id(name: str, props: dict) -> str:
    """Reproduce the ID hashing logic from Island.__post_init__."""
    props_hash = hashlib.sha256(
        json.dumps(props, sort_keys=True, default=str).encode()
    ).hexdigest()[:8]
    return f"{name}-{props_hash}"


class MockElement:
    """Minimal stub with a .render() method."""

    def __init__(self, html: str):
        self._html = html

    def render(self) -> str:
        return self._html


class MockHtmlObject:
    """Stub with a .__html__() method (but no .render())."""

    def __init__(self, html: str):
        self._html = html

    def __html__(self) -> str:
        return self._html


# ---------------------------------------------------------------------------
# IslandConfig
# ---------------------------------------------------------------------------


class TestIslandConfigDefaults:
    """Tests for IslandConfig default values."""

    def test_default_output_dir(self):
        """Default output_dir should be '_islands'."""
        config = IslandConfig()

        assert config.output_dir == "_islands"

    def test_default_strategy(self):
        """Default hydration strategy should be 'idle'."""
        config = IslandConfig()

        assert config.default_strategy == "idle"

    def test_default_debug_is_false(self):
        """Debug mode should be off by default."""
        config = IslandConfig()

        assert config.debug is False

    def test_custom_values_are_stored(self):
        """Custom values should be stored as supplied."""
        config = IslandConfig(output_dir="assets/islands", default_strategy="load", debug=True)

        assert config.output_dir == "assets/islands"
        assert config.default_strategy == "load"
        assert config.debug is True


# ---------------------------------------------------------------------------
# Island ID generation
# ---------------------------------------------------------------------------


class TestIslandIdGeneration:
    """Tests for Island._id computed in __post_init__."""

    def test_id_contains_name(self):
        """Generated ID should start with the island name."""
        island = Island(name="counter", component=lambda: None)

        assert island._id.startswith("counter-")

    def test_id_suffix_is_eight_chars(self):
        """The hash suffix should be exactly 8 hex characters."""
        island = Island(name="counter", component=lambda: None)

        suffix = island._id.split("-", 1)[1]
        assert len(suffix) == 8

    def test_id_is_deterministic(self):
        """Same name + props should always produce the same ID."""
        props = {"count": 0, "label": "Click me"}
        island_a = Island(name="btn", component=lambda: None, props=props)
        island_b = Island(name="btn", component=lambda: None, props=props)

        assert island_a._id == island_b._id

    def test_id_differs_for_different_props(self):
        """Different props should produce different IDs for the same name."""
        island_a = Island(name="btn", component=lambda: None, props={"count": 0})
        island_b = Island(name="btn", component=lambda: None, props={"count": 1})

        assert island_a._id != island_b._id

    def test_id_differs_for_different_names(self):
        """Different names with identical props should produce different IDs."""
        island_a = Island(name="alpha", component=lambda: None, props={"x": 1})
        island_b = Island(name="beta", component=lambda: None, props={"x": 1})

        assert island_a._id != island_b._id

    def test_id_matches_expected_hash(self):
        """ID should match the manually computed expected value."""
        props = {"value": 42}
        island = Island(name="widget", component=lambda: None, props=props)

        assert island._id == _expected_id("widget", props)

    def test_id_with_empty_props(self):
        """Empty props should still produce a valid ID."""
        island = Island(name="static", component=lambda: None)

        assert island._id == _expected_id("static", {})


# ---------------------------------------------------------------------------
# Island.render() - callable component
# ---------------------------------------------------------------------------


class TestIslandRenderCallable:
    """Tests for Island.render() with a plain callable component."""

    def test_callable_result_is_stringified(self):
        """A callable returning a plain value should be converted with str()."""

        def my_component():
            return "hello world"

        island = Island(name="greet", component=my_component)
        html = island.render()

        assert "hello world" in html

    def test_callable_receives_props(self):
        """Props should be passed as keyword arguments to the callable."""

        def label_component(text: str) -> str:
            return f"<span>{text}</span>"

        island = Island(name="label", component=label_component, props={"text": "Hi"})
        html = island.render()

        assert "<span>Hi</span>" in html

    def test_data_island_attribute_present(self):
        """Rendered div must carry data-island with the island name."""
        island = Island(name="myisland", component=lambda: "content")
        html = island.render()

        assert 'data-island="myisland"' in html

    def test_data_island_id_attribute_present(self):
        """Rendered div must carry data-island-id matching island._id."""
        island = Island(name="myisland", component=lambda: "content")
        html = island.render()

        assert f'data-island-id="{island._id}"' in html

    def test_data_hydrate_attribute_present(self):
        """Rendered div must carry data-hydrate matching the client strategy."""
        island = Island(name="myisland", component=lambda: "content", client="visible")
        html = island.render()

        assert 'data-hydrate="visible"' in html

    def test_default_hydrate_strategy_is_idle(self):
        """Default data-hydrate value should be 'idle'."""
        island = Island(name="myisland", component=lambda: "content")
        html = island.render()

        assert 'data-hydrate="idle"' in html

    def test_props_serialised_into_data_props(self):
        """Props should be serialised and HTML-escaped into data-props."""
        props = {"title": "Hello", "count": 3}
        island = Island(name="card", component=lambda **kw: "x", props=props)
        html = island.render()

        assert "data-props=" in html
        # Quotes in JSON are escaped to &quot;
        assert "&quot;" in html

    def test_no_data_props_when_empty_props(self):
        """data-props attribute should be absent when props is empty."""
        island = Island(name="static", component=lambda: "body")
        html = island.render()

        assert "data-props" not in html


# ---------------------------------------------------------------------------
# Island.render() - component with .render() method
# ---------------------------------------------------------------------------


class TestIslandRenderWithRenderMethod:
    """Tests for Island.render() when component returns an object with .render()."""

    def test_calls_render_on_result(self):
        """Should call .render() on the returned object."""
        element = MockElement("<p>Rich element</p>")

        def component_factory():
            return element

        island = Island(name="richcomp", component=component_factory)
        html = island.render()

        assert "<p>Rich element</p>" in html

    def test_render_result_is_inner_html(self):
        """The .render() output should appear as the inner HTML of the wrapper div."""
        inner = "<strong>bold</strong>"
        island = Island(name="bold", component=lambda: MockElement(inner))
        html = island.render()

        assert html.startswith("<div ")
        assert inner in html


# ---------------------------------------------------------------------------
# Island.render() - component with .__html__() method
# ---------------------------------------------------------------------------


class TestIslandRenderWithHtmlMethod:
    """Tests for Island.render() when callable returns an object with .__html__()."""

    def test_calls_dunder_html_when_no_render(self):
        """Should fall back to .__html__() when result has no .render()."""

        def component_factory():
            return MockHtmlObject("<em>italic</em>")

        island = Island(name="em", component=component_factory)
        html = island.render()

        assert "<em>italic</em>" in html


# ---------------------------------------------------------------------------
# Island.render() - non-callable component
# ---------------------------------------------------------------------------


class TestIslandRenderNonCallable:
    """Tests for Island.render() when component is not callable."""

    def test_non_callable_is_stringified(self):
        """A non-callable component should be converted with str()."""
        island = Island(name="raw", component="<b>static</b>")
        html = island.render()

        assert "<b>static</b>" in html


# ---------------------------------------------------------------------------
# Island.render() - client_only=True
# ---------------------------------------------------------------------------


class TestIslandRenderClientOnly:
    """Tests for Island.render() when client_only=True."""

    def test_placeholder_comment_is_used(self):
        """client_only island should render the loading placeholder comment."""
        island = Island(name="spa", component=lambda: "should not appear", client_only=True)
        html = island.render()

        assert "<!-- Island loading... -->" in html

    def test_component_is_not_called(self):
        """The component function should never be invoked for client_only islands."""
        called = []

        def spy_component():
            called.append(True)
            return "content"

        island = Island(name="spa", component=spy_component, client_only=True)
        island.render()

        assert called == []

    def test_hydration_attributes_still_present(self):
        """Hydration attributes must still be present for client_only islands."""
        island = Island(name="spa", component=lambda: None, client_only=True, client="load")
        html = island.render()

        assert 'data-island="spa"' in html
        assert 'data-hydrate="load"' in html


# ---------------------------------------------------------------------------
# Island.render() - media strategy
# ---------------------------------------------------------------------------


class TestIslandRenderMediaStrategy:
    """Tests for Island.render() with client='media' and a media query."""

    def test_data_media_attribute_present(self):
        """data-media should appear when client='media' and media is set."""
        island = Island(
            name="responsive",
            component=lambda: "content",
            client="media",
            media="(max-width: 768px)",
        )
        html = island.render()

        assert 'data-media="(max-width: 768px)"' in html

    def test_data_media_absent_for_non_media_strategy(self):
        """data-media should not appear when client strategy is not 'media'."""
        island = Island(
            name="responsive",
            component=lambda: "content",
            client="visible",
            media="(max-width: 768px)",
        )
        html = island.render()

        assert "data-media" not in html

    def test_data_media_absent_when_media_is_none(self):
        """data-media should not appear when media is None even if client='media'."""
        island = Island(
            name="responsive",
            component=lambda: "content",
            client="media",
            media=None,
        )
        html = island.render()

        assert "data-media" not in html


# ---------------------------------------------------------------------------
# Island.render() - error handling
# ---------------------------------------------------------------------------


class TestIslandRenderErrorHandling:
    """Tests for Island.render() error handling when the component raises."""

    def test_error_renders_comment(self):
        """A component that raises should produce an HTML comment with the error."""

        def broken_component():
            raise ValueError("something went wrong")

        island = Island(name="broken", component=broken_component)

        with patch("nitro.core.islands.warning"):
            html = island.render()

        assert "<!-- Error rendering island:" in html
        assert "something went wrong" in html

    def test_warning_is_called_on_error(self):
        """warning() should be called when the component raises."""

        def broken_component():
            raise RuntimeError("boom")

        island = Island(name="broken", component=broken_component)

        with patch("nitro.core.islands.warning") as mock_warning:
            island.render()

        mock_warning.assert_called_once()
        call_args = mock_warning.call_args[0][0]
        assert "broken" in call_args
        assert "boom" in call_args

    def test_wrapper_div_still_rendered_on_error(self):
        """Even when the component fails, the wrapper div must be present."""

        def broken_component():
            raise TypeError("bad type")

        island = Island(name="broken", component=broken_component)

        with patch("nitro.core.islands.warning"):
            html = island.render()

        assert html.startswith("<div ")
        assert 'data-island="broken"' in html


# ---------------------------------------------------------------------------
# Island.__str__()
# ---------------------------------------------------------------------------


class TestIslandStr:
    """Tests for Island.__str__() delegation."""

    def test_str_returns_render_output(self):
        """__str__ must return the same string as render()."""
        island = Island(name="str_test", component=lambda: "body text")

        assert str(island) == island.render()

    def test_str_and_render_are_identical(self):
        """str() and render() must produce byte-for-byte identical output."""
        props = {"a": 1, "b": "two"}
        island = Island(
            name="identical",
            component=lambda a, b: f"<p>{a} {b}</p>",
            props=props,
        )

        assert str(island) == island.render()


# ---------------------------------------------------------------------------
# IslandProcessor.process_html()
# ---------------------------------------------------------------------------


class TestIslandProcessorProcessHtml:
    """Tests for IslandProcessor.process_html()."""

    def test_injects_script_when_islands_present(self):
        """Should inject a <script> tag when data-island= attribute is found."""
        processor = IslandProcessor()
        html = '<div data-island="counter" data-island-id="counter-abc" data-hydrate="idle"></div>'

        result = processor.process_html(html)

        assert "<script>" in result

    def test_script_injected_before_body_close(self):
        """Script tag should be placed before </body> when present."""
        processor = IslandProcessor()
        html = (
            "<html><body>"
            '<div data-island="counter" data-island-id="c-abc" data-hydrate="idle"></div>'
            "</body></html>"
        )

        result = processor.process_html(html)

        script_pos = result.index("<script>")
        body_close_pos = result.index("</body>")
        assert script_pos < body_close_pos

    def test_noop_when_no_islands_present(self):
        """Should return HTML unchanged when no islands are present."""
        processor = IslandProcessor()
        html = "<html><body><p>Static content</p></body></html>"

        result = processor.process_html(html)

        assert result == html

    def test_inject_script_false_skips_injection(self):
        """Should not inject script when inject_script=False, even with islands."""
        processor = IslandProcessor()
        html = '<div data-island="counter" data-island-id="c-abc" data-hydrate="idle"></div>'

        result = processor.process_html(html, inject_script=False)

        assert "<script>" not in result
        assert result == html

    def test_appends_script_when_no_body_tag(self):
        """Should append script at the end when </body> is absent."""
        processor = IslandProcessor()
        html = '<div data-island="counter" data-island-id="c-abc" data-hydrate="idle"></div>'

        result = processor.process_html(html)

        assert result.endswith("</script>")

    def test_script_contains_hydration_logic(self):
        """The injected script should contain core hydration identifiers."""
        processor = IslandProcessor()
        html = '<div data-island="x" data-island-id="x-0" data-hydrate="idle"></div>'

        result = processor.process_html(html)

        assert "__registerIsland" in result
        assert "data-island" in result

    def test_empty_string_is_returned_unchanged(self):
        """An empty string has no islands and should pass through unchanged."""
        processor = IslandProcessor()

        result = processor.process_html("")

        assert result == ""

    def test_custom_config_is_used(self):
        """Processor should use the provided IslandConfig."""
        config = IslandConfig(debug=True)
        processor = IslandProcessor(config=config)

        assert processor.config.debug is True

    def test_default_config_created_when_none_supplied(self):
        """Processor should create a default IslandConfig when none is given."""
        processor = IslandProcessor()

        assert isinstance(processor.config, IslandConfig)
        assert processor.config.debug is False
