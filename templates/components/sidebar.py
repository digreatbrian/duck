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
    def on_create(self):
        self.style.setdefaults(SIDEBAR_STYLE)
        self.properties.setdefault(SIDEBAR_PROPS)
