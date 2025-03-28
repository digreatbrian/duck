"""
Icon component module.

Notes:
- This depends on your JS/CSS bundle you are using for icons.
"""
from duck.html.components import InnerHtmlComponent
from .link import Link


class IconLink(Link):
    """
    Icon Link component.
    """
    def on_create(self):
        super().on_create()
        self.style["color"] = "#ccc"


class Icon(InnerHtmlComponent):
    """
    Icon component.
    
    Args:
        icon_class (str): Icon class according to your custom JS/CSS Icon bundle.
    """
    def get_element(self):
        return "span"
        
    def on_create(self):
        super().on_create()
        if "icon_class" in self.kwargs:
            icon_class = self.kwargs.get('icon_class')
            self.properties["class"] = icon_class
