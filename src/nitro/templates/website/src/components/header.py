"""Header component."""

from ydnatl import Header as HTMLHeader, Nav, Link, Div, H1


def Header(site_name="My Website"):
    """Create a header component.

    Args:
        site_name: Name of the site to display

    Returns:
        Header element
    """
    header_elem = HTMLHeader(
        Div(
            H1(site_name),
            Nav(
                Link("Home", href="/"),
                Link("About", href="/about.html"),
            ),
        )
    )

    # Add classes
    header_elem.children[0].children[0].add_attribute("class", "logo")
    header_elem.children[0].children[1].add_attribute("class", "nav")
    header_elem.children[0].add_attribute("class", "header-content")
    header_elem.add_attribute("class", "header")

    return header_elem
