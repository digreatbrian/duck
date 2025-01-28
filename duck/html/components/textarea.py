"""
Textarea Html Component
"""

from duck.html.components import InnerHtmlComponent


class TextArea(InnerHtmlComponent):
    """
    HTML TextArea component.
    """

    def __init__(self,
                 properties: dict[str, str] = {},
                 style: dict[str, str] = {}):
        """
        Initialize the Textarea component.
        """
        textarea_style = {
            "padding": "10px",
            "border": "1px solid #ccc",
            "border-radius": "4px",
            "font-size": "14px",
        }
        textarea_style.update(style) if style else None  # update default style

        super().__init__("textarea", properties, textarea_style)
