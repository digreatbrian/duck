from duck.html.components import InnerHtmlComponent

from .link import Link


class IconLink(Link):
    def on_create(self):
        super().on_create()
        self.style["color"] = "#ccc"


class Icon(InnerHtmlComponent):
    def get_element(self):
        return "span"
        
    def on_create(self):
        super().on_create()
        if "icon_class" in self.kwargs:
            icon_class = self.kwargs.get('icon_class')
            self.properties["class"] = icon_class
