from duck.html.components import InnerHtmlComponent
from theme import Theme

class Link(InnerHtmlComponent):
    """
    HTML Link component.
    """
    def get_element(self):
        return "a"
        
    def on_create(self):
        link_props = {"classname": "link"}
        link_style = {
            "color": Theme.primary_color,
            "text-decoration": "none",
        }
        self.style.setdefaults(link_style)
        self.properties.setdefaults(link_props)
        
        if self.kwargs.get("url"):
            self.properties.setdefault("href", self.kwargs.get("url", '#'))
        
        if self.kwargs.get("text"):
            self.inner_body += self.kwargs.get("text", '')
