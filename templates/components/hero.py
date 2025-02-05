from duck.html.components import InnerHtmlComponent


HERO_STYLE = { # Default Hero style with Bootstrap 5
    "display": "flex",
    "flex-direction": "column",
    "justify-content": "center",
    "align-items": "center",
    "padding": "10px",
    "background-color": "#333",
    "color": "white",
}

class Hero(InnerHtmlComponent):
    """
    HTML Hero component.
    """
    def __init__(self, properties: dict[str, str] = {}, style: dict[str, str] = {}, **kwargs):
        """
        Initialize the Hero html component.
        """
        # Call the parent class (InnerHtmlComponent) initializer
        super().__init__("div", properties, style, **kwargs)
        
        # Add the Hero title
        if kwargs.get("title"):
            self.add_title(kwargs.get("title"))
        
        # Add the Hero subtitle
        if kwargs.get("subtitle"):
            self.add_subtitle(kwargs.get("subtitle"))
    
    def add_title(self, title: str, **kwargs):
        """
        Add a title to the Hero.
        """
        self.inner_body += f'<h1 id="hero_title">{title}</h1>'
    
    def add_subtitle(self, subtitle: str, **kwargs):
        """
        Add a subtitle to the Hero.
        """
        self.inner_body += f'<p id="hero_subtitle">{subtitle}</p>'
