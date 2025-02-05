"""
Textarea Html Component
"""

from duck.html.components import InnerHtmlComponent


class TextArea(InnerHtmlComponent):
    """
    HTML TextArea component.
    """
    def get_element(self):
        return "textarea"
    
    def on_create(self):
        textarea_style = {
            "padding": "10px",
            "border": "1px solid #ccc",
            "border-radius": DefaultTheme.border_radius,
            "font-size": DefaultTheme.normal_font_size,
        }
        self.style.setdefaults(textarea_style)
