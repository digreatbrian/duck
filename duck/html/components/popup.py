"""
Popup HTML Component.

This module defines a reusable `Popup` component that creates a full-screen popup overlay.
It includes an exit button (dependent on Bootstrap icons) and JavaScript functionality for opening and closing.
"""
import random

from duck.html.components.container import FlexContainer
from duck.html.components.script import Script
from duck.html.components.icon import Icon


class Popup(FlexContainer):
    """
    Popup HTML Component.

    This component creates a full-screen, dismissible popup overlay. It is designed to be hidden by default and
    can be displayed when needed. Clicking outside the popup content or pressing the close button will hide it.

    **Dependencies:**  
    - This component relies on **`Bootstrap Icons`** for the exit button.
    - It also includes `jQuery-based JavaScript` functions to manage popup behavior.

    **Features:**
    - Full-screen overlay with a semi-transparent background.
    - Click outside the popup to close it.
    - Includes a close button for easy dismissal.
    - Automatically moves itself to the `<body>` tag to prevent positioning issues.
    - Adjusts height dynamically to fit the viewport.
    - Provides a `showPopup()` function to open the popup.
    """

    def on_create(self):
        """Initialize and configure the popup component."""
        # Style settings for the popup
        self.style.update({
            "min-width": "100vw",
            "background-color": "black",
            "padding": "5px",
            "position": "fixed",
            "z-index": "5",
            "transition": "display 0.3s ease",
            "top": "0",
            "left": "0",
            "display": "none",  # Hidden by default
            "flex-direction": "column",
        })
        
        popup_name = "popup-" + str(random.randint(0, 1000))
        self.properties["class"] = "popup"
        self.properties["id"] = popup_name

        # JavaScript script to handle popup behavior
        script = Script(
            inner_body="""
                var popup_selector = '#%s';
                
                function movePopupToBody() {
                    var popup = $(popup_selector);  // Select popup using jQuery
                    
                    if (popup.length && popup.parent()[0] !== document.body) {
                        popup.appendTo('body');  // Move popup to body
                    }
                }

                function closePopup(popup) {
                    $(popup).css('display', 'none');
                }

                function showPopup() {
                    var popup = $(popup_selector);
                    movePopupToBody();  // Ensure it's properly placed in <body>
                    adjustPopupHeight();
                    popup.css('display', 'flex');  // Show popup with flex layout
                }

                function adjustPopupHeight() {
                    $(popup_selector).css('height', $(window).height() + 'px');  // Set height dynamically
                }

                // Ensure movePopupToBody is executed when the document is ready
                $(document).ready(function () {
                    movePopupToBody();
                    adjustPopupHeight();  // Adjust height on load

                    // Close popup when clicking outside its content
                    $(popup_selector).on('click', function (event) {
                        if ($(event.target).is(popup_selector)) {
                            closePopup(this);  // Close popup when clicking on background
                        }
                    });

                    // Adjust popup height when window resizes
                    $(window).resize(adjustPopupHeight);
                });
            """%(popup_name)
        )

        # Create an exit button inside a container
        exit_btn_container = FlexContainer()
        exit_btn_container.style.update({
            "padding": "5px",
            "justify-content": "flex-end",
        })

        exit_btn = Icon(icon_class="bi bi-x-circle")  # Bootstrap "X" icon
        exit_btn.style.update({
            "color": "#ccc",
            "font-size": "1.95rem",
        })
        exit_btn.properties["onclick"] = "closePopup($(this).closest('.popup'));"  # Close popup on click

        # Add the exit button inside its container
        exit_btn_container.add_child(exit_btn)

        # Add the close button container and script to the popup
        if not self.kwargs.get('no_exit_button'):
            self.add_child(exit_btn_container)
        self.add_child(script)
