from ydnatl import *

# from src.components.header import Header
# from src.components.hero import Hero
# from src.components.services import Services
# from src.components.footer import Footer
from src.pages.home import HomePage

if __name__ == "__main__":

    print(HomePage.render())

    # header = Fragment(
    #     Header(
    #         Link(href="/", content="Home", class_name="logo"),
    #         Nav(
    #             Link(href="/about", content="About"),
    #             Link(href="/services", content="Services"),
    #             Link(href="/contact", content="Contact"),
    #         )
    #     )
    # )

    # hero = Section(
    #     H1("Hero Section"),
    #     Paragraph("This is the hero section of the page.")
    # )

    # services = Section(
    #     H2("Our Services"),
    # )

    # footer = Footer(
    #     Paragraph("© 2024 My Website")
    # )

    # html = HTML(
    #     # head=Head(
    #     #     Title("My Website"),
    #     #     Meta(charset="UTF-8"),
    #     #     Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
    #     #     Link(rel="stylesheet", href="styles.css")
    #     # ),
    #     # body=Body(
    #     #     header,
    #     #     hero,
    #     #     services,
    #     #     footer
    #     # )
    # )

    # home_page = Fragment(
    #     header,
    #     hero,
    #     services,
    #     footer
    # )

    # print(home_page.render())

    # Copyright("asdadasd")
    # ecko scaffold --page HomePage --output src/pages/home_page.py
    # ecko generate --input src/pages/home_page.py --output dist/home_page.html
    # ecko serve --directory dist --port 8000
    # ecko build --input src/main.py --output dist/bundle.js
    # ecko test --input tests/ --reporter spec

    # verb scaffold --template basic
    # verb scaffold --list-templates
    # verb new --name my-website

    # src/
    # - pages/
    # - components/
    # - data/
    # - styles/
    # - public/
    # - tests/
    # - plugins/
    # build/
    # main.py
    # verb serve/s
    # verb build
    # verb test
    # verb docs
    # verb deploy --target github-pages / netlify / deploy-target.json

    # verb.sh/mcp -> MCP server for YDNATL

    # Premium:
    # - Hosting
    # - verb deploy --project machine-republic.com
    # verb cms
    # verb spam free form submissions

    # JSONDataStore(name="", path="")
    # CSVDataStore(name="", path="")
    # SQLDataStore(name=")
    # RESTDataStore(name="", base_url="", headers={}, auth=())
