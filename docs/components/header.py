from nitro_ui import Fragment, Header, Link, Nav


HeaderComponent = Fragment(
    Header(
        Link(href="/", content="Home", class_name="logo"),
        Nav(
            Link(href="/about", content="About"),
            Link(href="/services", content="Services"),
            Link(href="/contact", content="Contact"),
        ),
    )
)

HeaderComponent.on_before_render = lambda: print("Rendering HeaderComponent")
HeaderComponent.on_after_render = lambda: print("Rendered HeaderComponent")

# HeaderComponent.on_before_render = lambda self: print("Rendering HeaderComponent")
# HeaderComponent.on_after_render = lambda self: print("Rendered HeaderComponent")
