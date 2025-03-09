"""
Card component.
"""

from duck.html.components import Theme

from .container import FlexContainer


class Card(FlexContainer):
    def on_create(self):
        super().on_create()
        self.style["padding"] = Theme.padding
        self.style["min-height"] = "100px"
        self.style['text-align'] = 'center'
        self.style["flex-direction"] = "column"
        self.style["align-items"] = "center"
        self.style["justify-content"] = "center"
        self.style["border-radius"] = Theme.border_radius
        self.properties["class"] = "flex-card"
