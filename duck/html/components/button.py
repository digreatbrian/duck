"""
This module contains various types of Button components.
"""
from typing import Dict
from duck.html.components import Theme, InnerHtmlComponent


class Button(InnerHtmlComponent):
    """
    Basic button component.
    """
    def get_element(self):
        return "button"
    
    def on_create(self):
        btn_style = {
            "padding": "10px 20px",
            "cursor": "pointer",
            "transition": "background-color 0.3s ease",
            "border": "none",
            "border-radius": Theme.border_radius
        }  # default style
        
        self.style.setdefaults(btn_style)
        

class RoundedButton(Button):
    """
    Rounded button component.
    """
    def on_create(self):
        super().on_create()
        self.style["border-radius"] = "50%" # update button radius nomatter what


class FlatButton(Button):
    """
    Flat button component.
    """
    def on_create(self):
        super().on_create()
        self.style.setdefaults({
            "background-color": "transparent"
        })
    
    
class RaisedButton(Button):
    """
    Raised button component.
    """
    def on_create(self):
        super().on_create()
        self.style["box-shadow"] = "0 2px 2px rgba(0, 0, 0, 0.2)" # override box shadow nomatter what
