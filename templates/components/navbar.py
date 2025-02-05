from duck.html.components import InnerHtmlComponent

from .container import Container
from .link import Link

# Default Navbar style with Bootstrap 5
NAVBAR_STYLE = {
    "display": "flex",
    "justify-content": "space-between",
    "align-items": "center",
    "padding": "10px 20px",
    "background-color": "#333",
    "color": "white",
}

# Default Navbar properties
NAVBAR_PROPS = {
    "class": """
        navbar navbar-expand-lg navbar-dark bg-dark fixed-top shadow
        flex-row justify-content-between
    """, # links to the right and brand to the left
}

class NavBrand(InnerHtmlComponent):
    """
    HTML Navbar brand component.
    """
    def __init__(self, properties: dict[str, str] = {}, style: dict[str, str] = {}, **kwargs):
        """
        Initialize the Navbar brand html component.
        """
        # Call the parent class (InnerHtmlComponent) initializer
        super().__init__("a", properties, style, **kwargs)
        
        if kwargs.get("onclick"):
            self.properties["onclick"] = kwargs.get("onclick")
        
        # Add the brand image
        self.inner_body += f'<img src="{kwargs.get("image_src", "#")}" alt="{kwargs.get("alt", "brand")}" width="30" height="30" class="d-inline-block align-top">'


class Navbar(InnerHtmlComponent):
    """
    HTML Navbar component.
    """
    def __init__(self, properties: dict[str, str] = {}, style: dict[str, str] = {}, **kwargs):
        """
        Initialize the Navbar html component.
        """
        navbar_style = NAVBAR_STYLE.copy()
        navbar_props = NAVBAR_PROPS.copy()
        
        # Update default style with provided style
        navbar_style.update(style) if style else None
        navbar_props.update(properties) if properties else None
        
        # Call the parent class (InnerHtmlComponent) initializer
        super().__init__("nav", properties, navbar_style, **kwargs)
        
        # Add the Navbar brand
        self.add_brand(**kwargs.get("brand", {}))
        
        # Navbar links container
        links_container = InnerHtmlComponent("div", {"class": "collapse navbar-collapse", "id": "navbarNav"})
        
        # Add the Navbar links container
        links = kwargs.get("links", [])
        links = [Link(href=link.get("href", "#"), text=link.get("name", "Link"), style={"margin-right": "3px"}) for link in links]
        
        # Add the links to the Navbar
        links_container.add_children(links)
        
        # Add the Navbar links container to the Navbar
        self.add_child(links_container)
    
    def add_brand(self, **kwargs):
        """
        Add a brand to the Navbar.
        """
        self.add_child(NavBrand(**kwargs))
