from duck.html.components import InnerHtmlComponent

LINK_STYLE = {
    "color": "blue",
    "text-decoration": "none",
}


LINK_PROPS = {
    "classname": "link",
}

class Link(InnerHtmlComponent):
    """
    HTML Link component.
    """
    def __init__(self, properties: dict[str, str] = {}, style: dict[str, str] = {}, **kwargs):
        """
        Initialize the Link html component.
        """
        
        link_style = LINK_STYLE.copy()
        link_props = LINK_PROPS.copy()
        
        # Update default style with provided style
        link_style.update(style) if style else None
        link_props.update(properties) if properties else None
        
        if kwargs.get("href"):
            self.properties["href"] = kwargs.get("href")
            
        # Call the parent class (InnerHtmlComponent) initializer
        super().__init__("a", properties, style, **kwargs)
        
        if kwargs.get("text"):
            self.inner_body += kwargs.get("text")
