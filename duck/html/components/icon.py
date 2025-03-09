"""
Icon html component, this depends on your JS/CSS bundle you are using for icons.
"""
from duck.html.components import InnerHtmlComponent

from .link import Link


class IconLink(Link):
    """
    Link html component for an icon.
    """
    def on_create(self):
        super().on_create()
        self.style["color"] = "#ccc"


class Icon(InnerHtmlComponent):
    """
    Icon html component.
    
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
