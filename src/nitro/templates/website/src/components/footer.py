"""Footer component using nitro-ui."""

from nitro_ui import Footer as UIFooter, Paragraph, A


def Footer():
    """Create a footer component.

    Returns:
        Footer element
    """
    footer_elem = UIFooter(
        Paragraph(
            "Built with ",
            A("Nitro", href="https://github.com/nitro-sh/nitro-cli", target="_blank"),
            " and ",
            A("nitro-ui", href="https://github.com/nitrosh/nitro-ui", target="_blank"),
        ),
        class_name="footer",
    )
    return footer_elem
