from duck.html.components import InnerHtmlComponent


# Default Sidebar style with Bootstrap 5
SIDEBAR_STYLE = {
    "display": "flex",
    "flex-direction": "column",
    "padding": "10px",
    "background-color": "#333",
    "color": "white",
}

# Default Sidebar properties
SIDEBAR_PROPS = {
    "class": "nav flex-column",
}


class Sidebar(InnerHtmlComponent):
    """
    HTML Sidebar component.
    """
    def __init__(self, properties: dict[str, str] = {}, style: dict[str, str] = {}, **kwargs):
        """
        Initialize the Sidebar html component.
        """
        # Call the parent class (InnerHtmlComponent) initializer
        super().__init__("div", properties, style, **kwargs)
        
        for link in kwargs.get("links", []):
            # Add the link to the sidebar
            name, url, *_ = link.values()
            self.add_link(name, url)
    
    def add_link(self, name: str, href: str, **kwargs):
        """
        Add a link to the Sidebar.
        """
        self.inner_body += f'<a class="nav-link" href="{href}">{name}</a>'
