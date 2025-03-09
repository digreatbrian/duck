"""
Popup html component
"""
from duck.html.components.container import FlexContainer
from duck.html.components.script import Script
from duck.html.components.icon import Icon


class Popup(FlexContainer):
    """
    Popup html component - This depend on boostrap icons for exit button.
    """
    def on_create(self):
        self.style["min-width"] = "100vw"
        self.style["min-height"] = "100vh"
        self.style["background-color"] = "black"
        self.style["padding"] = "5px"
        self.style["position"] = "absolute"
        self.style["z-index"] = "5"
        self.style["transition"] = "display 0.3s ease"
        self.style["top"] = "0"
        self.style["left"] = "0"
        self.style["display"] = "none"
        self.style["flex-direction"] = "column"
        self.properties["class"] = "popup"
        
        script = Script(
            inner_body="""
                function movePopupToBody() {
                    var popup = $('.popup');  // Select popup using jQuery
                    if (popup.length && popup.parent()[0] !== document.body) {
                        popup.appendTo('body');  // Move popup to body
                    }
                }
                
                function closePopup(popup) {
                    $(popup).css('display', 'none');
                }
                
                // Ensure movePopupToBody is defined elsewhere in your code
                $(document).ready(function () {
                    movePopupToBody();
                    // Event handler for popup clicks
                    $('.popup').on('click', function (event) {
                        if ($(event.target).is('.popup')) {
                            closePopup(this);  // close the popup by using the reference
                        }
                    });
                });
                
                // Adjust the position of the popup when the window is resized
                $(window).resize(movePopupToBody);
                """
        )
        
        # Lets add toggle button to close popup
        exit_btn_container = FlexContainer()
        exit_btn_container.style["padding"] = "5px"
        exit_btn_container.style["justify-content"] = "flex-end"
        
        exit_btn = Icon(icon_class="bi bi-x-circle")
        exit_btn.style["color"] = "#ccc"
        exit_btn.style["font-size"] = "1.95rem"
        exit_btn.properties["onclick"] = "closePopup($(this).closest('.popup'));"
        
        # Add exit button to container
        exit_btn_container.add_child(exit_btn)
        
        # add exit button container
        self.add_child(exit_btn_container)
        
        # Add script for adding popup to topmost next body child
        self.add_child(script)
