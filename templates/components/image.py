from duck.html.components import NoInnerHtmlComponent


class Image(NoInnerHtmlComponent):
    """
    HTML Image component.
    """
    def get_element(self):
        return "img"
        
    def on_create(self):
        if self.kwargs.get("source"):
            self.properties["src"] = self.kwargs.get("source", '')
        
        if self.kwargs.get("alt"):
            self.properties["alt"] = self.kwargs.get("alt", '')
            
        if self.kwargs.get("width"):
            self.properties["width"] = self.kwargs.get("width", '')
            
        if self.kwargs.get("height"):
            self.properties["height"] = self.kwargs.get("height", '')


class CircularImage(Image):
    """
    HTML Circular Image component.
    """  
    def on_create(self):
        super().on_create()
        self.style["border-radius"] = "50%"
        