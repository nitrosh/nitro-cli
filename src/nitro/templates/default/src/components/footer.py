"""Footer component."""

from nitro_ui import Footer as UIFooter, Paragraph, Href


def Footer():
    """Create a footer component.

    Returns:
        Footer element
    """
    return UIFooter(
        Paragraph(
            "Built with ",
            Href("Nitro", href="https://github.com/nitro-sh/nitro-cli", target="_blank"),
            " and ",
            Href("nitro-ui", href="https://github.com/nitrosh/nitro-ui", target="_blank"),
        ),
        class_name="footer",
    )
