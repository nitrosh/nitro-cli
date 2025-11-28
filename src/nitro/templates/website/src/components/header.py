"""Header component using nitro-ui."""

from nitro_ui import Header as UIHeader, Nav, HtmlLink, Div, H1


def Header(site_name="My Website"):
    """Create a header component.

    Args:
        site_name: Name of the site to display

    Returns:
        Header element
    """
    # Create logo
    logo = H1(site_name)
    logo.add_attribute("class", "logo")

    # Create navigation
    nav = Nav(
        HtmlLink("Home", href="/"),
        HtmlLink("About", href="/about.html"),
    )
    nav.add_attribute("class", "nav")

    # Create header content wrapper
    header_content = Div(logo, nav)
    header_content.add_attribute("class", "header-content")

    # Create header element
    header_elem = UIHeader(header_content)
    header_elem.add_attribute("class", "header")

    return header_elem