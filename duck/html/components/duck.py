"""
Module containing Duck specific components.
"""
from .container import FlexContainer
from .image import Image


class MadeWithDuck(FlexContainer):
    """
    This is just a flex container component containing Duck's image alongside
    text named `Proudly made with Duck`
    """
    def on_create(self):
        super().on_create()
        from duck.etc.templatetags import static
        
        self.style["gap"] = "10px"
        self.style["align-items"] = "center"
        self.style["justify-content"] = "center"
        
        # Add image left
        image = Image(source=static('images/duck-logo.png'))
        image.style["object-fit"] = "contain"
        self.inner_body += image.to_string()
        
        # Add info
        self.inner_body += "Proudly made with Duck"
