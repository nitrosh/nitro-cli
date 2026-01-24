"""Footer component."""

from nitro_ui.html import footer, p, a


def Footer():
    """Create a footer component.

    Returns:
        Footer element
    """
    return footer(
        p(
            "Built with ",
            a("Nitro", href="https://github.com/nitro-sh/nitro-cli", target="_blank"),
            " and ",
            a("nitro-ui", href="https://github.com/nitro-sh/nitro-ui", target="_blank"),
        ),
        class_name="footer",
    )
