"""Islands architecture for partial hydration.

Islands allow interactive components to be hydrated on the client
while the rest of the page remains static HTML.

Hydration strategies:
- load: Hydrate immediately when page loads
- idle: Hydrate when browser is idle (requestIdleCallback)
- visible: Hydrate when component is visible (IntersectionObserver)
- media: Hydrate when media query matches
- interaction: Hydrate on first user interaction (click, focus, etc.)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional
import hashlib
import json

from ..utils import warning


# Hydration strategies
HydrationStrategy = Literal["load", "idle", "visible", "media", "interaction", "none"]


@dataclass
class IslandConfig:
    """Tunable settings for the islands hydration pipeline.

    Controls where island scripts are emitted, the default hydration
    strategy applied when an `Island` does not specify one, and debug
    logging in the injected runtime.

    Example:
        >>> from nitro import IslandConfig, IslandProcessor
        >>> processor = IslandProcessor(IslandConfig(default_strategy="visible"))
    """

    # Output directory for island scripts (relative to build)
    output_dir: str = "_islands"

    # Default hydration strategy
    default_strategy: HydrationStrategy = "idle"

    # Enable debug mode (adds logging)
    debug: bool = False


@dataclass
class Island:
    """An interactive component that hydrates on the client.

    Islands bridge static HTML and client-side interactivity: the server
    renders the component once into a wrapper `<div>` with `data-island-*`
    attributes, and the runtime injected by `IslandProcessor` hydrates it
    according to the configured strategy (`load`, `idle`, `visible`,
    `media`, `interaction`, or `none`).

    Attributes:
        name: Component name used by the client registry (`__registerIsland`).
        component: A callable or object that renders the server-side HTML.
            Callables are invoked with `**props`; nitro-ui elements returned
            by the callable are rendered via `.render()`.
        props: JSON-serializable props passed to the server render and
            forwarded to the client via `data-props`.
        client: Hydration strategy. See the module docstring for options.
        client_only: Skip server rendering; emit a placeholder comment.
        media: Media query used when `client="media"`.

    Example:
        >>> from nitro import Island
        >>> island = Island(
        ...     name="Counter",
        ...     component=lambda start: f"<span>{start}</span>",
        ...     props={"start": 0},
        ...     client="visible",
        ... )
    """

    name: str
    component: Any  # The component class/function
    props: Dict[str, Any] = field(default_factory=dict)
    client: HydrationStrategy = "idle"
    client_only: bool = False  # If True, don't render on server
    media: Optional[str] = None  # Media query for "media" strategy

    _id: str = field(default="", init=False)

    def __post_init__(self):
        # Generate unique ID for this island instance
        props_hash = hashlib.sha256(
            json.dumps(self.props, sort_keys=True, default=str).encode()
        ).hexdigest()[:8]
        self._id = f"{self.name}-{props_hash}"

    def render(self) -> str:
        """Render the island as HTML with hydration markers.

        Produces a `<div>` wrapping the server-rendered output (or a
        placeholder comment when `client_only` is True) and annotated with
        `data-island`, `data-island-id`, `data-hydrate`, and optionally
        `data-props` / `data-media` so the client runtime can match and
        hydrate it. Render failures are caught and surfaced as an HTML
        comment rather than propagated.

        Returns:
            A single `<div>…</div>` HTML fragment.

        Example:
            >>> Island(name="Hello", component=lambda: "<p>hi</p>").render()
            '<div data-island="Hello" ...><p>hi</p></div>'
        """
        # Render the component (server-side)
        if self.client_only:
            inner_html = "<!-- Island loading... -->"
        else:
            try:
                if callable(self.component):
                    result = self.component(**self.props)
                    # Handle nitro-ui components
                    if hasattr(result, "render"):
                        inner_html = result.render()
                    elif hasattr(result, "__html__"):
                        inner_html = result.__html__()
                    else:
                        inner_html = str(result)
                else:
                    inner_html = str(self.component)
            except Exception as e:
                warning(f"Failed to render island '{self.name}': {e}")
                safe_msg = str(e).replace("--", "- -")
                inner_html = f"<!-- Error rendering island: {safe_msg} -->"

        # Build hydration attributes
        attrs = [
            f'data-island="{self.name}"',
            f'data-island-id="{self._id}"',
            f'data-hydrate="{self.client}"',
        ]

        if self.props:
            props_json = json.dumps(self.props, default=str)
            # Escape for HTML attribute
            props_escaped = props_json.replace('"', "&quot;")
            attrs.append(f'data-props="{props_escaped}"')

        if self.media and self.client == "media":
            attrs.append(f'data-media="{self.media}"')

        attrs_str = " ".join(attrs)

        return f"<div {attrs_str}>{inner_html}</div>"

    def __str__(self) -> str:
        return self.render()


class IslandProcessor:
    """Post-process HTML to wire up island hydration.

    Scans rendered HTML for `data-island` markers and, if any are present,
    injects a small vanilla-JS runtime before `</body>` that discovers
    islands, loads props from `data-props`, and defers hydration per the
    strategy in `data-hydrate`.

    Example:
        >>> from nitro import IslandProcessor
        >>> html = IslandProcessor().process_html("<html>...</html>")
    """

    def __init__(self, config: Optional[IslandConfig] = None):
        """Initialize the processor, optionally with custom settings.

        Args:
            config: Runtime/output settings. Defaults to `IslandConfig()` when None.
        """
        self.config = config or IslandConfig()

    def generate_hydration_script(self) -> str:
        """Return the client-side hydration runtime as a JS source string.

        The script exposes `window.__registerIsland(name, component)` for
        registering components, discovers islands on DOMContentLoaded, and
        dispatches each to its strategy handler. Debug logging is included
        when `config.debug` is True.

        Returns:
            A string of JavaScript source, suitable for embedding in a
            `<script>` tag (no tag wrapper is included).
        """
        debug_code = (
            "console.log('[Islands] Initializing...');" if self.config.debug else ""
        )

        return f"""
(function() {{
  {debug_code}

  // Island component registry
  const components = {{}};

  // Register a component for hydration
  window.__registerIsland = function(name, component) {{
    components[name] = component;
    {f'console.log("[Islands] Registered:", name);' if self.config.debug else ''}
  }};

  // Hydrate a single island
  function hydrateIsland(el) {{
    const name = el.dataset.island;
    const props = el.dataset.props ? JSON.parse(el.dataset.props.replace(/&quot;/g, '"')) : {{}};

    const component = components[name];
    if (!component) {{
      console.warn('[Islands] Component not found:', name);
      return;
    }}

    try {{
      {f'console.log("[Islands] Hydrating:", name, props);' if self.config.debug else ''}
      const result = component(props);

      // Handle different return types
      if (typeof result === 'string') {{
        el.innerHTML = result;
      }} else if (result && result.mount) {{
        // For frameworks with mount methods
        result.mount(el);
      }} else if (result && result.render) {{
        el.innerHTML = result.render();
      }}

      el.dataset.hydrated = 'true';
    }} catch (err) {{
      console.error('[Islands] Error hydrating', name, err);
    }}
  }}

  // Strategy handlers
  const strategies = {{
    load: function(el) {{
      hydrateIsland(el);
    }},

    idle: function(el) {{
      if ('requestIdleCallback' in window) {{
        requestIdleCallback(() => hydrateIsland(el));
      }} else {{
        setTimeout(() => hydrateIsland(el), 200);
      }}
    }},

    visible: function(el) {{
      if ('IntersectionObserver' in window) {{
        const observer = new IntersectionObserver((entries) => {{
          entries.forEach((entry) => {{
            if (entry.isIntersecting) {{
              observer.disconnect();
              hydrateIsland(el);
            }}
          }});
        }}, {{ rootMargin: '200px' }});
        observer.observe(el);
      }} else {{
        hydrateIsland(el);
      }}
    }},

    media: function(el) {{
      const query = el.dataset.media;
      if (!query) {{
        hydrateIsland(el);
        return;
      }}

      const mql = window.matchMedia(query);
      if (mql.matches) {{
        hydrateIsland(el);
      }} else {{
        mql.addEventListener('change', function handler(e) {{
          if (e.matches) {{
            mql.removeEventListener('change', handler);
            hydrateIsland(el);
          }}
        }});
      }}
    }},

    interaction: function(el) {{
      const events = ['click', 'focus', 'touchstart', 'mouseenter'];
      const handler = () => {{
        events.forEach((e) => el.removeEventListener(e, handler));
        hydrateIsland(el);
      }};
      events.forEach((e) => el.addEventListener(e, handler, {{ once: true, passive: true }}));
    }}
  }};

  // Initialize all islands on page
  function initIslands() {{
    const islands = document.querySelectorAll('[data-island]:not([data-hydrated])');
    {f'console.log("[Islands] Found", islands.length, "islands");' if self.config.debug else ''}

    islands.forEach((el) => {{
      const strategy = el.dataset.hydrate || 'idle';
      const handler = strategies[strategy];

      if (handler) {{
        handler(el);
      }} else {{
        console.warn('[Islands] Unknown strategy:', strategy);
      }}
    }});
  }}

  // Run on DOM ready
  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', initIslands);
  }} else {{
    initIslands();
  }}
}})();
"""

    def process_html(
        self,
        html_content: str,
        inject_script: bool = True,
    ) -> str:
        """Inject the hydration runtime into HTML when islands are present.

        Returns the input unchanged when no `data-island=` markers exist, or
        when `inject_script` is False. Otherwise wraps
        `generate_hydration_script()` in a `<script>` tag and inserts it
        before `</body>`, appending to the document if no closing body tag
        is found.

        Args:
            html_content: Rendered HTML document to post-process.
            inject_script: Set False to skip runtime injection entirely,
                even when islands are present.

        Returns:
            HTML with the hydration runtime embedded, or the original string
            when no changes are needed.

        Example:
            >>> processor.process_html("<html><body>...</body></html>")
        """
        # Check if there are any islands
        if "data-island=" not in html_content:
            return html_content

        if not inject_script:
            return html_content

        # Generate and inject hydration script
        script = self.generate_hydration_script()
        script_tag = f"<script>{script}</script>"

        # Inject before closing body tag
        if "</body>" in html_content:
            html_content = html_content.replace("</body>", f"{script_tag}\n</body>")
        else:
            html_content += script_tag

        return html_content
