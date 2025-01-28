"""
Input Html Component
"""

from duck.html.components import NoInnerHtmlComponent


class Input(NoInnerHtmlComponent):
    """
    HTML Input component.
    """

    def __init__(self,
                 properties: dict[str, str] = {},
                 style: dict[str, str] = {}):
        """
        Initialize the Input component.

        Args:
            input_type (str): The type of input (e.g., text, password, email). Defaults to "text".
        """
        input_style = {
            "padding": "10px",
            "border": "1px solid #ccc",
            "border-radius": "4px",
            "font-size": "14px",
        }
        input_style.update(style) if style else None  # update default style

        super().__init__("input", properties, input_style)


class CSRFInput(NoInnerHtmlComponent):
    """
    Csrf HTML Input component.
    """

    def __init__(self, request):
        """
        Initialize the Input component.

        Args:
            request : The request object
        """
        from duck.settings import SETTINGS
        from duck.template.security.csrf import get_csrf_token

        super().__init__("input", False)
        self.properties["type"] = "hidden"
        self.properties["id"] = self.properties["name"] = SETTINGS[
            "CSRF_COOKIE_NAME"]
        self.properties["value"] = get_csrf_token(request)
