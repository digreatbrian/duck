"""
Checkbox Html Component
"""

from duck.html.components import NoInnerHtmlComponent


class Checkbox(NoInnerHtmlComponent):
    """
    HTML Checkbox component.
    
    Args:
        - checked (bool): Whether the checkbox is checked or not.
    """
    def get_element(self):
        return "input"
    
    def on_create(self):
        checkbox_style = {"margin": "10px", "cursor": "pointer"}
        self.style.setdefaults(checkbox_style)
        self.properties["type"] = "checkbox" # overwrite input type absolutely
        
        if self.kwargs.get('checked'):
            self.properties.setdefault("checked", "true")
