"""Islands architecture for partial hydration.

Islands allow interactive components to be hydrated on the client
while the rest of the page remains static HTML.

Hydration strategies:
- load: Hydrate immediately when page loads
- idle: Hydrate when browser is idle (requestIdleCallback)
- visible: Hydrate when component is visible (IntersectionObserver)
- media: Hydrate when media query matches
- interaction: Hydrate on first user interaction (click, focus, etc.)

Usage in templates:
    from nitro.core.islands import Island, island

    # Create an island with a component
    counter = Island(
        name="counter",
        component=Counter,
        props={"initial": 0},
        client="visible"  # Hydration strategy
    )

    # In your page:
    def render():
        return Div(
            H1("My Page"),
            counter.render(),  # Renders static HTML + hydration marker
        )
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional, Union
import hashlib
import json
import re

from ..utils import info, warning


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
        """Render the island with hydration markers.

        Returns:
            HTML string with island wrapper and hydration data
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
            props_escaped = props_json.replace('"', '&quot;')
            attrs.append(f'data-props="{props_escaped}"')

        if self.media and self.client == "media":
            attrs.append(f'data-media="{self.media}"')

        attrs_str = " ".join(attrs)

        return f'<div {attrs_str}>{inner_html}</div>'

    def __str__(self) -> str:
        return self.render()


def island(
    component: Any,
    name: Optional[str] = None,
    client: HydrationStrategy = "idle",
    **props
) -> Island:
    """Create an island from a component.

    This is a convenience function for creating islands inline.

    Args:
        component: The component to wrap
        name: Island name (auto-generated if not provided)
        client: Hydration strategy
        **props: Props to pass to the component

    Returns:
        Island instance
    """
    if name is None:
        # Try to get name from component
        if hasattr(component, "__name__"):
            name = component.__name__.lower()
        elif hasattr(component, "__class__"):
            name = component.__class__.__name__.lower()
        else:
            name = "island"

    return Island(
        name=name,
        component=component,
        props=props,
        client=client,
    )


class IslandRegistry:
    """Registry for tracking islands used in a build."""

    def __init__(self):
        self._islands: Dict[str, Island] = {}
        self._scripts: Dict[str, str] = {}

    def register(self, island: Island) -> None:
        """Register an island.

        Args:
            island: Island to register
        """
        self._islands[island._id] = island

    def get(self, island_id: str) -> Optional[Island]:
        """Get an island by ID.

        Args:
            island_id: Island ID

        Returns:
            Island or None
        """
        return self._islands.get(island_id)

    def register_script(self, name: str, script: str) -> None:
        """Register a client-side script for an island.

        Args:
            name: Island name
            script: JavaScript code
        """
        self._scripts[name] = script

    def get_all_scripts(self) -> Dict[str, str]:
        """Get all registered scripts.

        Returns:
            Dictionary of island name to script
        """
        return self._scripts

    def clear(self) -> None:
        """Clear all registered islands."""
        self._islands.clear()
        self._scripts.clear()


# Global registry
_registry = IslandRegistry()


def get_registry() -> IslandRegistry:
    """Get the global island registry.

    Returns:
        IslandRegistry instance
    """
    return _registry


class IslandProcessor:
    """Processes HTML to handle islands."""

    def __init__(self, config: Optional[IslandConfig] = None):
        """Initialize the island processor.

        Args:
            config: Island configuration
        """
        self.config = config or IslandConfig()
        self.registry = get_registry()

    def generate_hydration_script(self) -> str:
        """Generate the client-side hydration script.

        This script handles hydrating all islands based on their strategy.

        Returns:
            JavaScript code
        """
        debug_code = "console.log('[Islands] Initializing...');" if self.config.debug else ""

        return f'''
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
'''

    def process_html(
        self,
        html_content: str,
        inject_script: bool = True,
    ) -> str:
        """Process HTML and inject hydration script if islands are present.

        Args:
            html_content: HTML content
            inject_script: Whether to inject the hydration script

        Returns:
            Processed HTML
        """
        # Check if there are any islands
        if 'data-island=' not in html_content:
            return html_content

        if not inject_script:
            return html_content

        # Generate and inject hydration script
        script = self.generate_hydration_script()
        script_tag = f'<script>{script}</script>'

        # Inject before closing body tag
        if '</body>' in html_content:
            html_content = html_content.replace(
                '</body>',
                f'{script_tag}\n</body>'
            )
        else:
            html_content += script_tag

        return html_content

    def extract_islands(self, html_content: str) -> List[Dict]:
        """Extract all islands from HTML content.

        Args:
            html_content: HTML content

        Returns:
            List of island info dictionaries
        """
        pattern = re.compile(
            r'<div\s+data-island="([^"]+)"\s+data-island-id="([^"]+)"[^>]*>',
            re.IGNORECASE
        )

        islands = []
        for match in pattern.finditer(html_content):
            islands.append({
                "name": match.group(1),
                "id": match.group(2),
            })

        return islands

    def write_island_scripts(
        self,
        output_dir: Path,
        scripts: Dict[str, str],
    ) -> List[Path]:
        """Write island component scripts to files.

        Args:
            output_dir: Output directory
            scripts: Dictionary of island name to script content

        Returns:
            List of written file paths
        """
        islands_dir = output_dir / self.config.output_dir
        islands_dir.mkdir(parents=True, exist_ok=True)

        written = []
        for name, script in scripts.items():
            script_path = islands_dir / f"{name}.js"
            script_path.write_text(script)
            written.append(script_path)

        if written:
            info(f"Wrote {len(written)} island script(s)")

        return written


# Decorator for creating island components
def client_component(
    strategy: HydrationStrategy = "idle",
    name: Optional[str] = None,
):
    """Decorator to mark a component as a client-side island.

    Usage:
        @client_component(strategy="visible")
        def Counter(initial=0):
            return Div(f"Count: {initial}")

    Args:
        strategy: Hydration strategy
        name: Optional custom name

    Returns:
        Decorator function
    """
    def decorator(func):
        component_name = name or func.__name__.lower()

        def wrapper(**props):
            return Island(
                name=component_name,
                component=func,
                props=props,
                client=strategy,
            )

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper._is_island = True
        wrapper._strategy = strategy
        wrapper._component_name = component_name

        return wrapper

    return decorator


# Pre-defined island creators for common patterns
def lazy_island(component: Any, **props) -> Island:
    """Create a lazily-hydrated island (on visible).

    Args:
        component: Component to wrap
        **props: Component props

    Returns:
        Island instance
    """
    return island(component, client="visible", **props)


def eager_island(component: Any, **props) -> Island:
    """Create an eagerly-hydrated island (on load).

    Args:
        component: Component to wrap
        **props: Component props

    Returns:
        Island instance
    """
    return island(component, client="load", **props)


def interactive_island(component: Any, **props) -> Island:
    """Create an island that hydrates on interaction.

    Args:
        component: Component to wrap
        **props: Component props

    Returns:
        Island instance
    """
    return island(component, client="interaction", **props)


def static_island(component: Any, **props) -> Island:
    """Create an island that never hydrates (static only).

    Args:
        component: Component to wrap
        **props: Component props

    Returns:
        Island instance
    """
    return island(component, client="none", **props)
