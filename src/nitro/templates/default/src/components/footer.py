"""Footer component."""

from nitro_ui import Footer, Paragraph, Href


def SiteFooter():
    """Create a footer component.

    Returns:
        Footer element
    """
    return Footer(
        Paragraph(
            "Built with ",
            Href("Nitro", href="https://github.com/nitrosh/nitro-cli", target="_blank"),
            " and ",
            Href(
                "nitro-ui", href="https://github.com/nitrosh/nitro-ui", target="_blank"
            ),
        ),
        cls="footer",
    )
