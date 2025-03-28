"""
Navigation Bar Component Module.

This module defines reusable components for creating a fully customizable navigation bar.
It includes support for branding, navigation links, and a responsive design.
"""

from duck.html.components import (
    InnerHtmlComponent,
    Theme,
)
from .container import (
    Container,
    FlexContainer,
)
from .button import (
    Button,
    FlatButton,
)
from .link import Link
from .icon import Icon
from .image import Image
from .script import Script
from .style import Style


class NavbarBrand(Link):
    """
    Navigation Bar Brand Component.

    This component represents the brand section of the navigation bar. It is a clickable
    link that can contain a brand image, text, or both. It is primarily used within
    the `Navbar` component.

    Args:
        brand (dict): A dictionary containing brand details:
            * image_source (str): The URL of the brand image.
            * alt (str): Alternative text for the brand image.
            * url (str): The destination URL when the brand is clicked.
            * text (str): The text displayed next to the brand image.
    """

    def on_create(self):
        """Initialize and configure the NavbarBrand component."""
        if "brand" in self.kwargs:
            self.add_navbar_image()

        self.style["color"] = "none"
        self.properties["class"] = "navbar-brand me-auto"
        super().on_create()

    def add_navbar_image(self):
        """Adds a brand image and optional text to the NavbarBrand component."""
        brand = self.kwargs.get("brand", {})
        image_source = brand.get("image_source")
        alt = brand.get("alt", "")
        url = brand.get("url", "#")
        text = brand.get("text", "")

        self.kwargs.update({"url": url})

        if image_source:
            brand_image = Image(source=image_source)
            brand_image.properties["class"] = "nav-brand-image"
            brand_image.style["height"] = "40px"
            brand_image.style["width"] = "auto"

            if alt:
                brand_image.properties["alt"] = alt

            self.add_child(brand_image)

        if text:
            brand_text = FlexContainer(inner_body=text)
            brand_text.style["display"] = "inline-flex"
            brand_text.style["margin-left"] = "3px"
            brand_text.properties["class"] = "nav-brand-text"
            self.add_child(brand_text)


class NavbarLinks(InnerHtmlComponent):
    """
    Navigation Bar Links Component.

    This component contains a list of navigation links displayed in the navbar.

    Args:
        links (list): A list of dictionaries representing navigation links.
            Each dictionary should have:
            * text (str): The display text for the link.
            * url (str): The URL the link navigates to.
    """

    def get_element(self):
        return "ul"

    def on_create(self):
        """Initialize and configure the NavbarLinks component."""
        self.properties["class"] = "navbar-nav navbar-links d-flex gap-3"
        self.properties["id"] = "navbar-links"

        if "links" in self.kwargs:
            self.add_links()

    def add_links(self):
        """Adds navigation links to the component."""
        links = self.kwargs.get("links", [])

        for link_item in links:
            text = link_item.get("text", "")
            url = link_item.get("url", "#")
            link = Link(text=text, url=url, properties={"class": "nav-link active"})
            link.style["color"] = "#ccc"
            self.inner_body += f"<li class='nav-item'>{link.to_string()}</li>"


class NavbarContainer(FlexContainer):
    """
    Navbar Container Component.

    This component wraps and organizes all elements inside the navigation bar, including
    branding, toggler buttons for mobile, and navigation links.
    """

    def on_create(self):
        """Initialize and configure the NavbarContainer component."""
        super().on_create()
        self.properties["class"] = "container-fluid d-flex justify-content-between align-items-center"

        # Add Navbar Brand
        self.add_child(NavbarBrand(**self.kwargs))

        # Add Navbar Toggler (for mobile)
        navbar_toggler = FlatButton()
        navbar_toggler.style["outline"] = "none !important"
        navbar_toggler.style["background-color"] = "transparent"
        navbar_toggler.properties["class"] = "navbar-toggler"
        navbar_toggler.properties["onclick"] = "toggleCollapse($('.navbar-links-container'));"

        navbar_toggler_icon = Icon(icon_class="navbar-toggler-icon bi bi-list")
        navbar_toggler_icon.style["width"] = "16px"
        navbar_toggler_icon.style["height"] = "16px"
        navbar_toggler_icon.properties["alt"] = "menu"

        navbar_toggler.add_child(navbar_toggler_icon)
        self.add_child(navbar_toggler)

        # Add Navbar Links Container
        navbar_links_container = Container()
        navbar_links_container.properties["class"] = "navbar-links-container collapse navbar-collapse d-lg-flex align-items-center"
        navbar_links_container.style["justify-content"] = "end"

        # Add Navbar Links to their container
        navbar_links_container.add_child(NavbarLinks(**self.kwargs))
        self.add_child(navbar_links_container)

        # Add script for toggling navbar visibility
        script = Script(
            inner_body="""
                function toggleCollapse(elem) {
                    elem = $(elem);
                    if (elem.is(':hidden')) {
                        elem.css('display', 'flex');
                    } else {
                        elem.css('display', 'none');
                    }
                }
            """
        )
        self.add_child(script)


class Navbar(InnerHtmlComponent):
    """
    Navigation Bar Component.

    This component represents a full navigation bar with a brand logo, navigation links, and
    a responsive toggler button for mobile screens.

    Example Template Usage:
    
    ```django
    {% Navbar %}
        brand = {
            "image_source": "{% static 'images/logo.png' %}",
            "alt": "Duck Logo",
            "url": '{% resolve "home" fallback_url="#" %}',
            "text": "Duck logo"
        },
        links = [
            {"text": "Home", "url": "{% resolve 'home' fallback_url='#' %}"},
            {"text": "About", "url": "{% resolve 'about' fallback_url='#' %}"},
            {"text": "Services", "url": "{% resolve 'services' fallback_url='#' %}"},
            {"text": "Contact", "url": "{% resolve 'contact' fallback_url='#' %}"},
            {"text": "Consultation", "url": "{% resolve 'consultation' fallback_url='#' %}"},
            {"text": "Jobs", "url": "{% resolve 'jobs' fallback_url='#' %}"},
        ],
    {% endNavbar %}
    ```
    """

    def get_element(self):
        return "nav"

    def on_create(self):
        """Initialize and configure the Navbar component."""
        self.properties["class"] = "navbar navbar-expand-lg navbar-dark px-3"
        self.style["background-color"] = "rgba(100, 100, 100, .25)"

        # Add Navbar Container
        self.add_child(NavbarContainer(**self.kwargs))

        # Add responsive styles
        style = Style(
            inner_body="""
                @media (max-width: 768px){
                    .navbar-collapse {
                        justify-content: start !important;
                    }
                    .nav-brand-image {
                        height: 30px !important;
                    }
                }
            """
        )
        self.add_child(style)
