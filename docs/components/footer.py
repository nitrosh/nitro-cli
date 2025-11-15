from ydnatl import Fragment, Footer


class FooterComponent(Fragment):
    def __init__(self):
        super().__init__(Footer("© 2024 My Website"))
