"""Footer component."""

from ydnatl import Footer as HTMLFooter, Paragraph, Link


def Footer():
    """Create a footer component.

    Returns:
        Footer element
    """
    footer_elem = HTMLFooter(
        Paragraph(
            "Built with ",
            Link(
                "Nitro", href="https://github.com/nitro-sh/nitro-cli", target="_blank"
            ),
            " and ",
            Link("YDNATL", href="https://github.com/sn/ydnatl", target="_blank"),
        )
    )
    footer_elem.add_attribute("class", "footer")
    return footer_elem
