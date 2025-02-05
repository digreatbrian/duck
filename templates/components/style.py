from duck.html.components import InnerHtmlComponent


class Style(InnerHtmlComponent):
    """
    HTML Style component.
    """
    def __init__(self, properties: dict[str, str] = {}, style: dict[str, str] = {}, **kwargs):
        """
        Initialize the Style html component.
        """
        # Call the parent class (InnerHtmlComponent) initializer
        super().__init__("style", properties, style, **kwargs)
        if kwargs.get("selector"):
            self.properties["selector"] = kwargs.get("selector")
        
        if kwargs.get("text"):
            self.inner_body += kwargs.get("text")
        
        if kwargs.get("src"):
            self.properties["src"] = kwargs.get("src")
