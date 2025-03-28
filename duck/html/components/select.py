"""
Select HTML Component.

This module provides reusable `Select` and `Option` components for creating dropdown menus in HTML.
"""

from duck.html.components import (
    InnerHtmlComponent,
    Theme,
)


class Option(InnerHtmlComponent):
    """
    Represents an individual option within a `Select` dropdown.

    This component is used to define selectable items inside a `Select` component.

    **Example Usage:**
    ```py
    option = Option(inner_body="Option 1")
    select.add_child(option)
    ```

    This generates:
    ```html
    <option>Option 1</option>
    ```

    **Returns:**
        - An `<option>` HTML element.
    """

    def get_element(self):
        """Returns the HTML tag for the component."""
        return "option"


class Select(InnerHtmlComponent):
    """
    A reusable HTML `<select>` component for creating dropdown menus.

    This component generates a customizable `<select>` dropdown with options.

    **Args:**
        options (list[str], optional):  
            A list of options as text or HTML.  
            **Note:** The 'option' tag should not be included in individual options.

    **Example Usage:**
    ```py
    select = Select(
        options=[
            "Option 1",
            "Option 2",
            "Option 3"
        ]
    )
    component.add_child(select)
    ```

    This generates:
    ```html
    <select>
        <option>Option 1</option>
        <option>Option 2</option>
        <option>Option 3</option>
    </select>
    ```

    **Styling:**
    - Uses default styling based on the `Theme` class.
    - Can be customized using CSS styles.

    **Returns:**
        - A `<select>` HTML element.
    """

    def get_element(self):
        """Returns the HTML tag for the component."""
        return "select"

    def on_create(self):
        """Initializes the component with default styles and options."""
        select_style = {
            "padding": "10px",
            "border": "1px solid #ccc",
            "border-radius": Theme.border_radius,
            "font-size": Theme.normal_font_size,
        }
        self.style.setdefaults(select_style)

        if "options" in self.kwargs:
            for option_html in self.kwargs.get("options"):
                self.add_child(Option(inner_body=option_html))
