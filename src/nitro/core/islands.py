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
    """Configuration for islands."""

    # Output directory for island scripts (relative to build)
    output_dir: str = "_islands"

    # Default hydration strategy
    default_strategy: HydrationStrategy = "idle"

    # Enable debug mode (adds logging)
    debug: bool = False


@dataclass
class Island:
    """An interactive island component.

    Islands are components that need client-side JavaScript to function.
    They are rendered as static HTML on the server and hydrated on the client.
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
        props_hash = hashlib.md5(
            json.dumps(self.props, sort_keys=True, default=str).encode()
        ).hexdigest()[:8]
        self._id = f"{self.name}-{props_hash}"

    def render(self) -> str:
        """Render the island with hydration markers."""
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
                inner_html = f"<!-- Error rendering island: {e} -->"

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
    """Processes HTML to handle islands."""

    def __init__(self, config: Optional[IslandConfig] = None):
        self.config = config or IslandConfig()

    def generate_hydration_script(self) -> str:
        """Generate the client-side hydration script."""
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
        """Process HTML and inject hydration script if islands are present."""
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
