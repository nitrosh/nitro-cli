"""Footer component."""

from nitro_ui import Footer as UIFooter, Paragraph, Link


def Footer():
    """Create a footer component.

    Returns:
        Footer element
    """
    return UIFooter(
        Paragraph(
            "Built with ",
            Link("Nitro", href="https://github.com/nitro-sh/nitro-cli", target="_blank"),
            " and ",
            Link("nitro-ui", href="https://github.com/nitrosh/nitro-ui", target="_blank"),
        ),
        class_name="footer",
    )
