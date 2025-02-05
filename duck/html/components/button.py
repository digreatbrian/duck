"""
Button Html Components
"""
from typing import Dict
from duck.html.components import DefaultTheme, InnerHtmlComponent


class Button(InnerHtmlComponent):
    """
    HTML Button component.
    """
    def get_element(self):
        return "button"
    
    def on_create(self):
        btn_style = {
            "padding": "10px 20px",
            "cursor": "pointer",
            "transition": "background-color 0.3s ease",
            "border": "none",
        }  # default style
        
        self.style.setdefaults(btn_style)
        self.style.setdefaults(DefaultTheme.get_base_style())


class RoundedButton(Button):
    """
    HTML Rounded Button component.
    """
    def on_create(self):
        super().on_create()
        self.style["border-radius"] = "50%" # update button radius nomatter what


class FlatButton(Button):
    """
    HTML FlatButton component.
    """
    def on_create(self):
        super().on_create()
        
        self.style.setdefaults({
            "background-color": "transparent",
            "color": DefaultTheme.bg_color,
        })
    
    
class RaisedButton(Button):
    """
    HTML RaisedButton component.
    """
    def on_create(self):
        super().on_create()
        self.style["box-shadow"] = "0 2px 2px rgba(0, 0, 0, 0.2)" # override box shadow nomatter what
