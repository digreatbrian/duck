
from theme import Theme

from .container import FlexContainer


class Card(FlexContainer):
    def on_create(self):
        self.style["padding"] = Theme.padding
        self.style["min-height"] = "300px"
        self.style['text-align'] = 'center'
        self.style["flex-direction"] = "column"
        self.style["align-items"] = "center"
        self.style["justify-content"] = "center"
        self.style["border-radius"] = Theme.border_radius
        super().on_create()
        

class ServiceCard(Card):
    def on_create(self):
        super().on_create()
        self.style["min-height"] = "300px"
        self.style['text-align'] = 'center'
        self.style["flex-direction"] = "column"
        self.style["align-items"] = "center"
        self.style["justify-content"] = "center"
        self.style["border"] = "1px solid #ccc"
        
        self.properties["class"] = 'service-card card'
        # Add service card image
        
        # Add heading and subheading to card
        heading, subheading = self.kwargs.get('heading', ''), self.kwargs.get('subheading', '')
        self.inner_body += f"<h2 class='heading'>{heading}</h2>"
        self.inner_body += f"<p class='heading'>{subheading}</p>"


class ServiceCards(FlexContainer):
    def on_create(self):
        super().on_create()
        self.style["flex-wrap"] = "wrap"
        self.style['grid-template-columns'] = 'repeat(auto-fit, minmax(300px, 1fr))'
        self.style['gap'] = '5px'
        self.style['justify-content'] = 'flex-start'
        self.style["margin-bottom"] = "10px"
        self.style["align-items"] = "center"
        
        self.properties["class"] = "service-cards"
        
        if "services" in self.kwargs:
            
            for service_item in self.kwargs.get("services"):
                service_heading, subheading = service_item.get('heading', ''), service_item.get('subheading', '')
                
                # Create and add info to service card
                service_card = ServiceCard(heading=service_heading, subheading=subheading)
                
                # Add service card
                self.add_child(service_card)

