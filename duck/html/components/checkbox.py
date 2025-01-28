"""
Checkbox Html Component
"""

from duck.html.components import NoInnerHtmlComponent


class CheckBoxError(Exception):
    """
    Checkbox related errors
    """


class Checkbox(NoInnerHtmlComponent):
    """
    HTML Checkbox component.
    """

    def __init__(self,
                 properties: dict[str, str] = {},
                 style: dict[str, str] = {}):
        """
        Initialize the Checkbox component.
        """
        if properties:
            if "type" in properties:
                input = properties.get("type", "").lower().strip()
                if input == "checkbox":
                    properties.pop(
                        "type"
                    )  # remove the input key in properties as it might change the state of InputField
                else:
                    if input:
                        raise CheckBoxError(
                            f"Key 'input' in properties is only allowed to be 'checkbox' not '{input}' "
                        )

        checkbox_properties = {"type": "checkbox"}
        checkbox_style = {"margin": "10px", "cursor": "pointer"}
        (checkbox_properties.update(properties) if properties else None
         )  # update default properties
        checkbox_style.update(style) if style else None  # update default style

        super().__init__("input", checkbox_properties, checkbox_style)
