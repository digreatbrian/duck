"""
Basic Hero component.
"""
from duck.html.components import Theme

from .container import FlexContainer


class Hero(FlexContainer):
    """
    HTML Hero component.
    
    Args:
        background_html: Html for hero background.
    """
    def on_create(self):
        super().on_create()
        self.style["flex-direction"] = "column"
        self.style["width"] = "100%"
        self.style["height"] = "100vh"
        self.style["padding"] = "15px 15px 30px 15px"
        self.properties["class"] = "hero display-flex justify-content-center"
