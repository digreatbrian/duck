"""
Style HTML Component.

This module defines a reusable `Style` component for embedding CSS styles within an HTML document.
"""

from duck.html.components import InnerHtmlComponent


class Style(InnerHtmlComponent):
    """
    Style HTML Component.

    The `Style` component allows developers to define and embed custom CSS styles directly within an HTML page.
    It can be used to dynamically style elements without needing an external stylesheet.

    **Features:**
    - Supports inline CSS.
    - Can be dynamically added to any component.
    - Enables styling customization for other components.

    **Example Usage:**
    ```py
    style = Style(
        inner_body='''
            .custom-popup {
                background-color: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 10px;
                border-radius: 5px;
            }
        '''
    )
    component.add_child(style)
    ```

    This will generate the following HTML output:
    ```html
    <style>
        .custom-popup {
            background-color: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
        }
    </style>
    ```

    **Notes:**
    - The `inner_body` parameter must contain valid CSS code.
    - This component is intended for **inline styles** and does not support linking to external CSS files.
    - Styles defined within this component will apply globally unless scoped using class or ID selectors.
    """

    def get_element(self):
        """Returns the HTML tag for the component."""
        return "style"
