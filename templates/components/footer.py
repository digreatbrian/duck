from duck.html.components import InnerHtmlComponent

from theme import Theme
from .container import FlexContainer


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


class Footer(InnerHtmlComponent):
    def get_element(self):
        return "footer"
    
    def on_create(self):
        self.style["padding"] = Theme.padding
        self.style["width"] = "100%"
        self.footer_items = FooterItems(**self.kwargs)
        
        # Add footer items
        self.inner_body += self.footer_items.to_string()
        
        # Add copyright info
        self.inner_body += "<p class='text-center'>&copy; 2025 Yannick Consultany. All rights reserved.</p>"
        