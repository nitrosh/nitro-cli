"""Header component using nitro-ui."""

from nitro_ui import Header as UIHeader, Nav, A, Div, H1


def Header(site_name="My Blog"):
    """Create a header component.

    Args:
        site_name: Name of the site to display

    Returns:
        Header element
    """
    # Create logo
    logo = H1(site_name, class_name="logo")

    # Create navigation
    nav = Nav(A("Home", href="/"), A("About", href="/about.html"), class_name="nav")

    # Create header content wrapper
    header_content = Div(logo, nav, class_name="header-content")

    # Create header element
    header_elem = UIHeader(header_content, class_name="header")

    return header_elem
