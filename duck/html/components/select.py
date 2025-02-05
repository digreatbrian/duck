"""
Select Html Component
"""

from duck.html.components import (
    InnerHtmlComponent,
    DefaultTheme,
)


class Option(InnerHtmlComponent):
    def get_element(self):
        return "option"


class Select(InnerHtmlComponent):
    """
    HTML Select component.
    """
    def get_element(self):
        return "select"
    
    def on_create(self):
        select_style = {
            "padding": "10px",
            "border": "1px solid #ccc",
            "border-radius": DefaultTheme.border_radius,
            "font-size": DefaultTheme.normal_font_size,
        }
        self.style.setdefaults(select_style)
        
        if "options" in self.kwargs:
            for option_html in self.kwargs.get("options"):
                self.add_child(Option(inner_body=option_html))
