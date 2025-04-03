"""
Hero component module.
"""
from duck.html.components import Theme
from .container import FlexContainer


class Hero(FlexContainer):
    """
    Basic Hero component.
    """
    def on_create(self):
        super().on_create()
        self.style["flex-direction"] = "column"
        self.style["width"] = "100%"
        self.style["height"] = "100vh"
        self.style["justify-content"] = "center"
        self.style["overflow"] = "hidden"
        self.properties["class"] = "hero"
