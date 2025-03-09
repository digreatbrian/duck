"""
Select Html Component
"""

from duck.html.components import (
    InnerHtmlComponent,
    Theme,
)


class Option(InnerHtmlComponent):
    def get_element(self):
        return "option"


class Select(InnerHtmlComponent):
    """
    HTML Select component.
    
    Args:
        options (list[str]): List of options as text/html, make sure you remove 'option' tag from individual options.
    """
    def get_element(self):
        return "select"
    
    def on_create(self):
        select_style = {
            "padding": "10px",
            "border": "1px solid #ccc",
            "border-radius": Theme.border_radius,
            "font-size": Theme.normal_font_size,
        }
        self.style.setdefaults(select_style)
        
        if "options" in self.kwargs:
            for option_html in self.kwargs.get("options"):
                self.add_child(Option(inner_body=option_html))
