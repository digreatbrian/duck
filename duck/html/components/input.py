"""
Input components module.
"""

from duck.html.components import (
    NoInnerHtmlComponent,
    Theme,
)
from .container import FlexContainer


class BaseInput(NoInnerHtmlComponent):
    """
    Base Input component.
    """
    def get_element(self):
        return "input"
    
    def on_create(self):
         style = {
            "padding": "10px",
            "border": "1px solid #ccc",
            "border-radius": Theme.border_radius,
            "font-size": Theme.normal_font_size,
         }
         self.style.setdefaults(style)
         
         if self.kwargs.get("value"):
             self.properties.setdefault("value", self.kwargs.get("value"))


class Input(BaseInput):
    """
    Input component.
    
    Args:
         type (str): The type of input, e.g. text, url, etc.
         name (str): Name of the input component.
         placeholder (str): Placeholder for input component.
         required (bool): Whether the field is required or not.
         maxlength (int): The maximum allowed characters.
     """
    def on_create(self):
        self.properties["min-width"] = "50%"
        self.properties["min-height"] = "60px"
        
        super().on_create()
        
        if "type" in self.kwargs:
            self.properties["type"] = self.kwargs.get('type') or ''
        
        if "name" in self.kwargs:
            self.properties["name"] = self.kwargs.get('name') or ''
        
        if "placeholder" in self.kwargs:
            placeholder = self.kwargs.get('placeholder') or ''
            self.properties["placeholder"] = placeholder
       
        if "required" in self.kwargs:
            self.properties["required"] = "true"
       
        if "maxlength" in self.kwargs:
           self.properties["maxlength"] = str(self.kwargs.get('maxlength')) or ''  


class InputWithLabel(FlexContainer):
    """
    InputWithLabel component which contains a label alongside an input component.
    
    Args:
        label_text (str): Text for the label
        input (HtmlComponent): Any html component (e.g fileinput.FileDragAndDrop), preferrebly Input component.
        
    Example Usage:
        fullname = InputWithLabel(
            label_text="Full Name",
            input=Input(
                type="text",
                name="fullname",
                placeholder="Full Name",
                required=True,
                maxlength=64,
            )
        )
        
        email = InputWithLabel(
            label_text="Email",
            input=Input(
                type="email",
                name="email",
                placeholder="Email",
                required=True,
                maxlength=64,
            )
        )
        
    """
    def on_create(self):
        self.style["gap"] = "10px"
        self.style["flex-direction"] = "column"
        super().on_create()
        
        if "label_text" in self.kwargs:
            label_text = self.kwargs.get('label_text', '')
            label = f"<label>{label_text}</label>"
            self.inner_body += label
        
        if "input" in self.kwargs:
            inputfield = self.kwargs.get('input', '')
            if inputfield:
                inputfield = inputfield.to_string()
                self.inner_body += inputfield


class CSRFInput(Input):
    """
    Csrf Input component - This component is useful in situations where you don't want to use the
    csrf_token tag. You only need to parse a request to generate csrfmiddleware field so as to avoid
    cross site request forgery attacks.
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
        self.properties["name"] = 'csrfmiddlewaretoken'
        self.properties["value"] = get_csrf_token(self.request)
