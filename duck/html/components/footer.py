from duck.html.components import InnerHtmlComponent
from duck.html.components import Theme

from .container import FlexContainer
from .image import Image
from .style import Style
from .link import Link


class FooterBlock(FlexContainer):
    def on_create(self):
        super().on_create()
        self.style["flex-direction"] = "column"
        
        if "heading" in self.kwargs:
            heading = self.kwargs.get('heading', '')
            self.inner_body += f"<h2 class='footer-heading'>{heading}</h2>"
       
        if 'elements' in self.kwargs:
           for element in self.kwargs.get('elements', []):
               # Element is an html element
               self.inner_body += element


class FooterItems(FlexContainer):
    def on_create(self):
        super().on_create()
        self.style["gap"] = "10px"
        
        if "footer_items" in self.kwargs:
             for heading, elements in self.kwargs.get('footer_items', {}).items():
                 footer_block = FooterBlock(heading=heading, elements=elements)
                 self.add_child(footer_block)


class MadeWithDuck(FlexContainer):
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
        

class Footer(InnerHtmlComponent):
    """
    Footer Html Component,
    
    Args:
        footer_items (dict): Dictionary containing footer items. A mapping of headings and their elements.
        copyright (str): Copyright info.
        
    Example Template Usage:
        {% Footer %}
           footer_items = {
             "Company": [
               '{% Link %}text="About Us", url="{% resolve 'about' fallback_url='#' %}"{% endLink %}',
               '{% Link %}text="Contact Us", url="{% resolve 'contact' fallback_url='#' %}"{% endLink %}',
               '{% Link %}text="Our Services", url="{% resolve 'services' fallback_url='#' %}"{% endLink %}',
             ], # Quick links
             "Legal": [
               '{% Link %}text="Privacy Policy", url="{% resolve 'privacy' fallback_url='#' %}"{% endLink %}',
               '{% Link %}text="Terms & Conditions", url="{% resolve 'tos' fallback_url='#' %}"{% endLink %}',
             ],
           },
           copyright="&copy; 2025 Duck. All rights reserved.",
         {% endFooter %}
    """
    def get_element(self):
        return "footer"
    
    def on_create(self):
        self.style["padding"] = Theme.padding
        self.style["width"] = "100%"
        self.footer_items = FooterItems(**self.kwargs)
        
        # Add footer items
        self.inner_body += self.footer_items.to_string()
        
        # Add made with Duck
        self.inner_body += Link(
            inner_body=MadeWithDuck().to_string(),
            url="https://github.com/digreatbrian/duck").to_string()
        
        # Add copyright info
        if self.kwargs.get('copyright'):
            copyright = self.kwargs.get('copyright') or ''
            self.inner_body += f"<p class='text-center'>{copyright}</p>"
        
        # Add style
        style = Style(
            inner_body="""
                @media (max-width: 768px){
                    footer {
                          font-size: .8rem;
                      }
                      
                      footer p {
                          font-size: .8rem !important;
                      }
                      
                      footer img {
                          width: 25px;
                          height: 25px;
                          margin-top: 5px;
                          margin-bottom: 5px;
                      }
                  }
            """
        )
        self.add_child(style)
