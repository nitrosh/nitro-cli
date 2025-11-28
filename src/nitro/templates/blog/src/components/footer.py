"""Footer component using nitro-ui."""

from nitro_ui import Footer as UIFooter, Paragraph, Anchor


def Footer():
    """Create a footer component.

    Returns:
        Footer element
    """
    footer_elem = UIFooter(
        Paragraph(
            "Built with ",
            Anchor(
                "Nitro", href="https://github.com/nitro-sh/nitro-cli", target="_blank"
            ),
            " and ",
            Anchor("nitro-ui", href="https://github.com/nitrosh/nitro-ui", target="_blank"),
        )
    )
    footer_elem.add_attribute("class", "footer")
    return footer_elem
