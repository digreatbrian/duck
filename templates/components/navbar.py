from duck.html.components import InnerHtmlComponent

from theme import Theme

from .container import Container, FlexContainer
from .link import Link
from .image import Image


class NavbarBrand(Link):
    def on_create(self):
        self.style["color"] = "none"
        self.properties["class"] = "navbar-brand me-auto"
        super().on_create()
        
        if "brand" in self.kwargs:
            self.add_navbar_image()
   
    def add_navbar_image(self):
       brand = self.kwargs.get("brand")
       image_source = brand.get("image_source")
       alt = brand.get("alt")
       
       # Add Navbar Image
       brand_image = Image(source=image_source)
       if alt:
           brand_image.properties["alt"] = alt
       self.add_child(brand_image)
       

class NavbarLinks(InnerHtmlComponent):
    def get_element(self):
        return "ul"
    
    def on_create(self):
        self.properties["class"] = "navbar-nav d-flex gap-3"
        self.properties["id"] = "navbar-links"
        if self.kwargs.get("links"):
            self.add_links()
            
    def add_links(self):
        links: list[str, str] = self.kwargs.get("links")
        for link_item in links:
            text, url = link_item["text"], link_item["url"]
            link = Link(text=text, url=url, properties={"class": "nav-link active"})
            link.style["color"] = "#ccc"
            self.inner_body += "<li class='nav-item'>" + link.to_string() + "</li>"


class NavbarContainer(FlexContainer):
    def on_create(self):
        super().on_create()
        self.properties['class'] = "container-fluid d-flex justify-content-between align-items-center"
        
        # Add Navbar Brand
        self.inner_body += NavbarBrand(**self.kwargs).to_string()
        
        #  Navbar Toggler (Mobile)
        navbar_toggler = '''
        <button class="navbar-toggler d-lg-none" type="button" data-bs-toggle="collapse" data-bs-target="#navbar-nav">
            <span class="navbar-toggler-icon"></span>
        </button>'''
        self.inner_body += navbar_toggler
        
        # Add Navbar Nav
        navbar_nav = Container()
        navbar_nav.properties["class"] = "collapse navbar-collapse d-lg-flex justify-content-end align-items-center"
        navbar_nav.properties["id"] = "navbar-nav"
        
        # Add Navbar Link to Navbar Nav
        navbar_nav.add_child(NavbarLinks(**self.kwargs))
        
        # Finally add Navbar Nav to Navbar Container
        self.inner_body += navbar_nav.to_string()


class Navbar(InnerHtmlComponent):
    def get_element(self):
        return "nav"
        
    def on_create(self):
        self.properties["class"] = "navbar navbar-expand-lg navbar-dark px-3"
        self.style["background-color"] = 'rgba(100, 100, 100, .25)'
        self.inner_body += NavbarContainer(**self.kwargs).to_string()
