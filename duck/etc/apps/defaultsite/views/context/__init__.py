"""
Module containing function `get_default_context` for retrieving Duck's default site context.
"""

from duck.shortcuts import resolve
from duck.version import server_version


def get_default_context() -> dict:
    """
    Returns the context for the Duck's default site.
    """
    duck_image = "/duck-static/images/duck-cover.png"
    about_image = "/duck-static/images/about-us.jpg"
    favicon = "/duck-static/images/duck-favicon.png"
    kofi_donate_img = "/duck-static/images/kofi_donate_img.png"
    home = resolve("ducksite.home", absolute=False)
    about = resolve("ducksite.about", absolute=False)
    contact = resolve("ducksite.contact", absolute=False)

    duck_default_context = {
        "home": home,
        "about": about,
        "contact": contact,
        "server_version": server_version,
        "duck_image": duck_image,
        "about_image": about_image,
        "kofi_donate_img": kofi_donate_img,
        "favicon": favicon,
        "repo_url": "https://github.com/digreatbrian/duck.git",
    }
    return duck_default_context
