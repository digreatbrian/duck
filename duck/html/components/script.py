"""
Script HTML Component.

This module defines a reusable `Script` component for embedding JavaScript code within an HTML document.
"""

from duck.html.components import InnerHtmlComponent


class Script(InnerHtmlComponent):
    """
    Script HTML Component.

    The `Script` component allows developers to embed JavaScript code within an HTML page dynamically.
    It can be used to define inline scripts that interact with other components.

    **Features:**
    - Supports inline JavaScript execution.
    - Can be dynamically added to any component.
    - Provides flexibility for defining custom client-side logic.

    **Example Usage:**
    ```py
    script = Script(
        inner_body='''
            function showAlert() {
                alert("Hello, world!");
            }
        '''
    )
    component.add_child(script)
    ```

    This will generate the following HTML output:
    ```html
    <script>
        function showAlert() {
            alert("Hello, world!");
        }
    </script>
    ```

    **Notes:**
    - Ensure that the JavaScript code provided in `inner_body` is properly formatted.
    - This component does not support external script sources (`src` attribute); it is designed for inline scripts.
    """

    def get_element(self):
        """Returns the HTML tag for the component."""
        return "script"
