"""
Textarea HTML Component.

This module provides a customizable `TextArea` component for handling multi-line text input in HTML forms.
"""

from duck.html.components import Theme
from duck.html.components import InnerHtmlComponent


class TextArea(InnerHtmlComponent):
    """
    A reusable HTML `<textarea>` component for multi-line text input.

    **Args:**
        name (str, optional):  
            The name attribute of the textarea, used for form submissions.

        placeholder (str, optional):  
            Placeholder text displayed inside the textarea before user input.

        required (bool, optional):  
            Whether the textarea is a required field in a form.

        maxlength (int, optional):  
            The maximum number of characters allowed in the textarea.

    **Example Usage:**
    ```py
    textarea = TextArea(
        name="user_message",
        placeholder="Enter your message...",
        required=True,
        maxlength=500
    )
    component.add_child(textarea)
    ```

    **Generates:**
    ```html
    <textarea name="user_message" placeholder="Enter your message..." required maxlength="500"></textarea>
    ```

    **Default Styling:**
    - Uses padding, borders, and font settings from the `Theme` class.
    - Minimum width is set to `50%` and minimum height to `80px`.

    **Returns:**
        - A `<textarea>` HTML element.
    """

    def get_element(self):
        """Returns the HTML tag for the component."""
        return "textarea"

    def on_create(self):
        """Initializes the component with default styles and attributes."""
        # Apply default styling
        textarea_style = {
            "padding": "10px",
            "border": "1px solid #ccc",
            "border-radius": Theme.border_radius,
            "font-size": Theme.normal_font_size,
        }
        self.style.setdefaults(textarea_style)

        # Set default properties
        self.properties["min-width"] = "50%"
        self.properties["min-height"] = "80px"

        # Assign properties based on arguments
        if "name" in self.kwargs:
            self.properties["name"] = self.kwargs.get("name", "")

        if "placeholder" in self.kwargs:
            self.properties["placeholder"] = self.kwargs.get("placeholder", "")

        if self.kwargs.get("required", False):
            self.properties["required"] = "true"

        if "maxlength" in self.kwargs:
            self.properties["maxlength"] = str(self.kwargs.get("maxlength", ""))
