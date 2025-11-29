from ydnatl import Fragment, H1

from src.components.header import HeaderComponent


# HomePage = Fragment(HeaderComponent, H1("Welcome to the Home Page"))


class HomePage(Fragment):
    def __init__(self):
        super().__init__(HeaderComponent, H1("Welcome to the Home Page"))

    def scoped_css(self):
        return {"h1": {"color": "red"}}
