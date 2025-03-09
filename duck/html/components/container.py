from duck.html.components import InnerHtmlComponent


class Container(InnerHtmlComponent):
    """
    HTML Container component.
    
    Args:
        inner_body (str): Body for the component.
    """
    def get_element(self):
        return "div"


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
