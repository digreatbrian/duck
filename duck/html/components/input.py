"""
Input Html Component
"""

from duck.html.components import (
    NoInnerHtmlComponent,
    DefaultTheme,
)


class Input(NoInnerHtmlComponent):
    """
    HTML Input component.
    """
    def get_element(self):
        return "input"
    
    def on_create(self):
         style = {
            "padding": "10px",
            "border": "1px solid #ccc",
            "border-radius": DefaultTheme.border_radius,
            "font-size": DefaultTheme.normal_font_size,
         }
         self.style.setdefaults(style)
         
         if self.kwargs.get("value"):
             self.properties.setdefault("value", self.kwargs.get("value"))


class CSRFInput(Input):
    """
    Csrf HTML Input component.
    """
    def __init__(self, request,):
        self.request = request
        super().__init__()
        
    def on_create(self):
        from duck.settings import SETTINGS
        from duck.template.csrf import get_csrf_token
        
        # empty all styles and props
        self.style.clear()
        self.properties.clear()
        self.properties["type"] = "hidden"
        self.properties["id"] = self.properties["name"] = SETTINGS["CSRF_COOKIE_NAME"]
        self.properties["value"] = get_csrf_token(self.request)
