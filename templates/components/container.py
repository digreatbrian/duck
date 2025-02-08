from duck.html.components import InnerHtmlComponent


class Container(InnerHtmlComponent):
    """
    HTML Container component.
    """
    def get_element(self):
        return "div"
        
    def on_create(self):
        self.inner_body += self.kwargs.get("body", "")
        

class FlexContainer(Container):
    """
    A container with flexbox layout.
    """
    def on_create(self):
        self.style.setdefault("display", "flex")


class GridContainer(Container):
    """
    A container using CSS grid layout.
    """
    def on_create(self):
        self.style.setdefault("display", "grid")


class Card(Container):
    """
    A styled container resembling a card.
    """
    def on_create(self):
        default_style = {
            "border": "1px solid #ddd",
            "border-radius": "8px",
            "padding": "16px",
            "box-shadow": "0 2px 4px rgba(0, 0, 0, 0.1)"
        }
        self.style.setdefaults(default_style)


class FluidContainer(Container):
    """
    A full-width container.
    """
    def on_create(self):
        self.style.setdefault("width", "100%")


class FixedContainer(Container):
    """
    A container with a fixed maximum width.
    """
    def on_create(self):
        default_style = {
            "max-width": "1200px",
            "margin": "0 auto",
            "padding": "16px"
        }
        self.style.setdefaults(default_style)
