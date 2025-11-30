"""Header component."""

from nitro_ui import Header as UIHeader, Nav, Link, Div, H1


def Header(site_name="My Site"):
    """Create a header component.

    Args:
        site_name: Name of the site to display

    Returns:
        Header element
    """
    logo = H1(site_name, class_name="logo")
    nav = Nav(
        Link("Home", href="/"),
        Link("About", href="/about.html"),
        class_name="nav",
    )
    header_content = Div(logo, nav, class_name="header-content")
    return UIHeader(header_content, class_name="header")
