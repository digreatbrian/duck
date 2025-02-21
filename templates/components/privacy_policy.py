from .container import FlexContainer
from .style import Style
from theme import Theme


class Block(FlexContainer):
    def on_create(self):
        super().on_create()
        self.style["flex-direction"] = "column"
        self.style["gap"] = "5px"
        self.style["padding"] = "5px"
        

class PrivacyPolicyPage(FlexContainer):
    def on_create(self):
        super().on_create()
        self.style["flex-direction"] = "column"
        self.style["padding"] = "5px"
        self.style["border"] = "1px solid #ccc"
        self.style["border-radius"] = Theme.border_radius
        self.style["color"] = "#ccc"
        self.style["gap"] = "5px"
        self.properties["class"] = "privacy-policy-page"
        
        # Add page global style
        style = Style(
            inner_body="""
              .privacy-policy-page h2 {
                font-size: 1.5rem;
              }
            """
        )
        self.add_child(style)
