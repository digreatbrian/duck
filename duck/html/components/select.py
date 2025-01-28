"""
Select Html Component
"""

from duck.html.components import InnerHtmlComponent


class Select(InnerHtmlComponent):
    """
    HTML Select component.
    """

    def __init__(
        self,
        options: list[str],
        properties: dict[str, str] = {},
        style: dict[str, str] = {},
    ):
        """
        Initialize the Select component.

        Args:
            options (list): List of options for the select element.
            properties (optional, dict[str, str]): Component properties/attributes
            style (optional, dict[str, str]): Component style properties
        """
        assert isinstance(
            options, list
        ), f"Argument options should be a list of Options for the select component not {type(options)}"
        self.options = options
        select_style = {
            "padding": "10px",
            "border": "1px solid #ccc",
            "border-radius": "4px",
            "font-size": "14px",
        }
        select_style.update(style) if style else None  # update default style

        super().__init__("select", properties, select_style)

    def to_string(self, add_style: bool = True):
        """
        Returns the string representation of the HTML select component.

        Args:
            add_style (bool, optional): Whether to add CSS style to the HTML element. Defaults to True.

        Returns:
            str: The string representation of the HTML select component.
        """
        inner_prop_string = self.get_inner_properties_string()
        elem_string = f"<{self.element}"
        if inner_prop_string:
            elem_string += f" {inner_prop_string}"

        if add_style:
            css = self.get_inner_css_string()
            if css:
                elem_string += f' style="{css}"'

        elem_string += ">"
        for option in self.options:
            elem_string += f'<option value="{option}">{option}</option>'
        elem_string += f"</{self.element}>"
        return elem_string
