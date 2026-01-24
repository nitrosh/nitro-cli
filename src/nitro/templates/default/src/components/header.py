"""Header component."""

from nitro_ui.html import header, nav, a, div, h1


def Header(site_name="My Site"):
    """Create a header component.

    Args:
        site_name: Name of the site to display

    Returns:
        Header element
    """
    logo = h1(site_name, class_name="logo")
    navigation = nav(
        a("Home", href="/"),
        a("About", href="/about.html"),
        class_name="nav",
    )
    header_content = div(logo, navigation, class_name="header-content")
    return header(header_content, class_name="header")
