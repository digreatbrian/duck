"""
Container components module.
"""
from duck.html.components import HtmlComponent, InnerHtmlComponent


class Container(InnerHtmlComponent):
    """
    Basic Container component derived from <div> tag.
    
    Args:
        inner_body (str): Body for the component.
    """
    def get_element(self):
        return "div"
    
    def set_background(
        self,
        component: HtmlComponent,
        bg_size: str = 'cover',
        repeat: str = "no-repeat",
        position: str = "center center",
        z_index: str = "-999",
    ):
        """
        Attach a component as a background with optional styling and default full-size fallback.
    
        Args:
            component (HtmlComponent): The component to use as the background.
            bg_size (str): CSS background-size value (e.g., 'cover', 'contain', or specific dimensions).
            repeat (str): CSS background-repeat value (e.g., 'no-repeat', 'repeat', 'repeat-x').
            position (str): CSS background-position value (e.g., 'center center', 'top left').
            z_index (str): Z-index to assign to the background component (as a string).
        """
        if not isinstance(component, HtmlComponent):
            raise TypeError(
                f"Component argument should be an instance of HtmlComponent, not {type(component).__name__}"
            )
    
        if component in self.children:
            raise ValueError("Component is already attached as a child.")
    
        # Set default width/height if missing
        if "width" not in component.style and "width" not in component.properties:
            component.style["width"] = "100%"
        
        if "height" not in component.style and "height" not in component.properties:
            component.style["height"] = "100%"
    
        # Background-related styling
        component.style["z-index"] = z_index
        component.style["background-size"] = bg_size
        component.style["background-repeat"] = repeat
        component.style["background-position"] = position
        component.style["position"] = "absolute"
    
        # Insert as first child to render behind other components
        self.children.insert(0, component)


class FlexContainer(Container):
    """
    Flex container component.
    """
    def on_create(self):
        self.style.setdefault("display", "flex")


class GridContainer(Container):
    """
    Grid container component.
    """
    def on_create(self):
        self.style.setdefault("display", "grid")


class FluidContainer(Container):
    """
    A full-width container component.
    """
    def on_create(self):
        self.style.setdefault("width", "100%")


class FixedContainer(Container):
    """
    Container component with a fixed maximum width.
    """
    def on_create(self):
        default_style = {
            "max-width": "1200px",
            "margin": "0 auto",
            "padding": "16px"
        }
        self.style.setdefaults(default_style)
