"""
Textarea Html Component
"""
from duck.html.components import Theme
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
            "border-radius": Theme.border_radius,
            "font-size": Theme.normal_font_size,
        }
        self.style.setdefaults(textarea_style)


class TextArea(TextArea):
     """
     TextArea html component.
     
     Args:
         name (str): Name of textarea
         placeholder (str): Placeholder for textarea
         required (bool): Whether the field is required or not.
         maxlength (int): The maximum allowed characters.
     """
     
     def on_create(self):
        self.properties["min-width"] = "50%"
        self.properties["min-height"] = "80px"
        super().on_create()
        
        if "name" in self.kwargs:
            self.properties["name"] = self.kwargs.get('name') or ''
        
        if "placeholder" in self.kwargs:
            placeholder = self.kwargs.get('placeholder') or ''
            self.properties["placeholder"] = placeholder
        
        if "required" in self.kwargs:
            self.properties["required"] = "true"
            
        if "maxlength" in self.kwargs:
           self.properties["maxlength"] = str(self.kwargs.get('maxlength')) or ''
