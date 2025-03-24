"""
Label component module.
"""
from duck.html.components import Theme, InnerHtmlComponent


class Label(InnerHtmlComponent):
    """
    Basic Label component.
    """
    def get_element(self):
        return "label"
    
    def on_create(self):
        if "text" in self.kwargs:
            text = self.kwargs.get('text') or ''
            self.inner_body += text
