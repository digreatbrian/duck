"""
Button Html Components
"""
from typing import Dict
from duck.html.components import DefaultTheme, InnerHtmlComponent


class Button(InnerHtmlComponent):
    """
    HTML Button component.
    """

    def __init__(self,
                 properties: Dict[str, str] = {},
                 style: Dict[str, str] = {}):
        """
        Initialize the FlatButton component.
        """
        btn_style = {
            "padding": "10px 20px",
            "cursor": "pointer",
            "transition": "background-color 0.3s ease",
            "border": "none",
        }  # default style

        btn_style.update(style) if style else None  # update default style

        super().__init__("button", properties, btn_style)


class RoundedButton(InnerHtmlComponent):
    """
    HTML Rounded Button component.
    """

    def __init__(self,
                 properties: Dict[str, str] = {},
                 style: Dict[str, str] = {}):
        """
        Initialize the CircularButton component.
        """
        btn_style = {
            "padding": "10px 20px",
            "cursor": "pointer",
            "transition": "background-color 0.3s ease",
            "border-radius": "50%",
        }
        btn_style.update(DefaultTheme.get_base_style())
        btn_style.update(style) if style else None  # update default style

        super().__init__("button", properties, btn_style)


class FlatButton(InnerHtmlComponent):
    """
    HTML FlatButton component.
    """

    def __init__(self,
                 properties: dict[str, str] = {},
                 style: dict[str, str] = {}):
        """
        Initialize the FlatButton component.
        """
        btn_style = {
            "padding": "10px 20px",
            "cursor": "pointer",
            "transition": "background-color 0.3s ease",
            "border": "none",
            "background-color": "transparent",
            "color": DefaultTheme.bg_color,
        }
        btn_style.update(style) if style else None  # update default style

        super().__init__("button", properties, btn_style)


class RaisedButton(InnerHtmlComponent):
    """
    HTML RaisedButton component.
    """

    def __init__(self,
                 properties: dict[str, str] = {},
                 style: dict[str, str] = {}):
        """
        Initialize the RaisedButton component.
        """
        btn_style = {
            "padding": "10px 20px",
            "cursor": "pointer",
            "transition": "background-color 0.3s ease",
            "box-shadow": "0 2px 2px rgba(0, 0, 0, 0.2)",
        }
        btn_style.update(DefaultTheme.get_base_style())
        btn_style.update(style) if style else None  # update default style

        super().__init__("button", properties, btn_style)
