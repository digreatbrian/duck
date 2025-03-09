from duck.html.components import InnerHtmlComponent, Theme
from .container import (
    Container,
    FlexContainer,
)
from .button import (
    Button,
    FlatButton,
)
from .link import Link
from .icon import Icon
from .image import Image
from .script import Script
from .style import Style


class NavbarBrand(Link):
    def on_create(self):
        # Set default styles and properties
        
        # Check if 'brand' exists in kwargs and call add_navbar_image if present
        if "brand" in self.kwargs:
            self.add_navbar_image()
        
        self.style["color"] = "none"
        self.properties["class"] = "navbar-brand me-auto"
        super().on_create()
        
   
    def add_navbar_image(self):
        brand = self.kwargs.get("brand", {})
        image_source = brand.get("image_source")
        alt = brand.get("alt", "")
        url = brand.get('url', '#')
        text = brand.get('text', '')
        
        self.kwargs.update({'url': url})
        
        if image_source:  # Only add image if the source is provided
            brand_image = Image(source=image_source)
            brand_image.properties['class'] = "nav-brand-image"
            brand_image.style["height"] = "50px"
            brand_image.style["width"] = "auto"
            
            brand_text = FlexContainer(inner_body=text)
            brand_text.style["display"] = "inline-flex"
            brand_text.style["margin-left"] = "3px"
            brand_text.properties["class"] = "nav-brand-text"
            
            if alt:
                brand_image.properties["alt"] = alt
            self.add_child(brand_image)
            
            if text:
                self.add_child(brand_text)


class NavbarLinks(InnerHtmlComponent):
    def get_element(self):
        return "ul"
    
    def on_create(self):
        # Set the class and id for the navbar links
        self.properties["class"] = "navbar-nav navbar-links d-flex gap-3"
        self.properties["id"] = "navbar-links"
        
        # Check if links are provided and add them
        if "links" in self.kwargs:
            self.add_links()
            
    def add_links(self):
        # Ensure links are a list of dictionaries with 'text' and 'url'
        links = self.kwargs.get("links", [])
        
        for link_item in links:
            text = link_item.get("text", "")
            url = link_item.get("url", "#")
            link = Link(text=text, url=url, properties={"class": "nav-link active"})
            link.style["color"] = "#ccc"
            # Add each link wrapped in a list item
            self.inner_body += f"<li class='nav-item'>{link.to_string()}</li>"


class NavbarContainer(FlexContainer):
    def on_create(self):
        super().on_create()
        # Set class properties for container
        self.properties['class'] = "container-fluid d-flex justify-content-between align-items-center"
        
        # Add Navbar Brand
        self.add_child(NavbarBrand(**self.kwargs))
        
        # Add Navbar Toggler (for mobile)
        navbar_toggler = FlatButton()
        navbar_toggler.style["outline"] = "none !important"
        navbar_toggler.style["background-color"] = "transparent"
        navbar_toggler.properties["class"] = "navbar-toggler"
        navbar_toggler.properties["onclick"] = "toggleCollapse($('.navbar-links-container'));"
        
        navbar_toggler_icon = Icon(icon_class="navbar-toggler-icon bi bi-list")
        navbar_toggler_icon.style["width"] = "16px"
        navbar_toggler_icon.style["height"] = "16px"
        navbar_toggler_icon.properties["alt"] = "menu"
        
        # Add nav toggler and its icon
        navbar_toggler.add_child(navbar_toggler_icon)
        self.add_child(navbar_toggler)
        
        # Add Navbar Links Container
        navbar_links_container = Container()
        navbar_links_container.properties["class"] = "navbar-links-container collapse navbar-collapse d-lg-flex align-items-center"
        navbar_links_container.style["justify-content"] = "end"
        
        # Add Navbar Links to their container
        navbar_links_container.add_child(NavbarLinks(**self.kwargs))
        
        # Finally, add Navbar Links container
        self.add_child(navbar_links_container)
        
        # Add a global nav bar script
        script = Script(
            inner_body="""
                function toggleCollapse(elem) {
                    elem = $(elem);
                
                    if (elem.is(':hidden')) {
                        elem.css('opacity', 0).css('display', 'flex'); // Make it visible but transparent
                        elem.stop(true).animate({
                            opacity: 1,
                        }, 500);
                    } else {
                        elem.stop(true).animate({
                            opacity: 0,
                        }, 500, function() {
                            elem.css('display', 'none');  // Set display to 'none' after animation
                        });
                    }
                }
            """
        )
        # finally add script
        self.add_child(script)


class Navbar(InnerHtmlComponent):
    """
    Navbar html component.
    
    Example Template Usage:
        {% Navbar %}
              brand = {
               "image_source": "{% static 'images/logo.png' %}",
               "alt": "Duck Logo",
               "url": '{% resolve "home" fallback_url="#" %}',
               "text": "Duck logo"
             },
             links = [
               {"text": "Home", "url": "{% resolve 'home' fallback_url='#' %}"},
               {"text": "About", "url": "{% resolve 'about' fallback_url='#' %}"},
               {"text": "Services", "url": "{% resolve 'services' fallback_url='#' %}"},
               {"text": "Contact", "url": "{% resolve 'contact' fallback_url='#' %}"},
               {"text": "Consultation", "url": "{% resolve 'consultation' fallback_url='#' %}"},
               {"text": "Jobs", "url": "{% resolve 'jobs' fallback_url='#' %}"},
            ],
           {% endNavbar %}
    """
    def get_element(self):
        return "nav"
        
    def on_create(self):
        # Set Navbar class and background color
        self.properties["class"] = "navbar navbar-expand-lg navbar-dark px-3"
        self.style["background-color"] = 'rgba(100, 100, 100, .25)'
        
        # Add Navbar Container
        self.add_child(NavbarContainer(**self.kwargs))
        
        # Add style
        style = Style(
            inner_body="""
                @media (max-width: 768px){
                     .navbar-collapse {
                          justify-content: start !important;
                      }
                      
                      .nav-brand-image {
                          height: 30px !important;
                      }
                  }
            """
        )
        self.add_child(style)
