from duck.html.components import NoInnerHtmlComponent


class Image(NoInnerHtmlComponent):
    """
    HTML Image component.
    """
    def __init__(self, properties: dict[str, str] = {}, style: dict[str, str] = {}, **kwargs):
        """
        Initialize the Image html component.
        """
        # Call the parent class (NoInnerHtmlComponent) initializer
        super().__init__("img", properties, style, **kwargs)
        
        if kwargs.get("onclick"):
            self.properties["onclick"] = kwargs.get("onclick")
          
        if kwargs.get("src"):
            self.properties["src"] = kwargs.get("src")
        
        if kwargs.get("alt"):
            self.properties["alt"] = kwargs.get("alt")
            
        if kwargs.get("width"):
            self.properties["width"] = kwargs.get("width")
            
        if kwargs.get("height"):
            self.properties["height"] = kwargs.get("height")
        
        