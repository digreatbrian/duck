from duck.html.components import InnerHtmlComponent


class Container(InnerHtmlComponent):
    """
    HTML Container component.
    """
    def __init__(self, properties: dict[str, str] = {}, style: dict[str, str] = {}, **kwargs):
        """
        Initialize the Container html component.
        """
        # Call the parent class (InnerHtmlComponent) initializer
        super().__init__("div", properties, style, **kwargs)
        
        # Add the Container body
        self.inner_body += kwargs.get("body", "")
