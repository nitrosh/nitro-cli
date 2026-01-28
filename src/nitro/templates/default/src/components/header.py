"""Header component."""

from nitro_ui import Header, Nav, Href, Div, H1


def SiteHeader(site_name="My Site"):
    """Create a header component.

    Args:
        site_name: Name of the site to display

    Returns:
        Header element
    """
    logo = H1(site_name, cls="logo")
    navigation = Nav(
        Href("Home", href="/"),
        Href("About", href="/about.html"),
        cls="nav",
    )
    header_content = Div(logo, navigation, cls="header-content")
    return Header(header_content, cls="header")
