
from theme import Theme

from .container import FlexContainer
from .image import Image
from .style import Style


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
        
        # Add heading and subheading to card
        heading, subheading = self.kwargs.get('heading', ''), self.kwargs.get('subheading', '')
        
        # Add service card image
        if "image_source" in self.kwargs:
            image_source = self.kwargs.get('image_source', '')
            image = Image(source=image_source)
            image.style["border_radius"] = Theme.border_radius
            image.style["object-fit"] = "contain"
            
            # Add image
            self.inner_body += image.to_string()
        
        # Add service card icon
        if "icon_class" in self.kwargs:
            icon_class =  self.kwargs.get('icon_class', '')
            icon = f"<span class='{icon_class} icon'></span>"
            
            # Add icon and icon style
            icon_style = Style()
            icon_style.inner_body = """
                .service-card .icon {
                    display: block;
                    font-size: 3rem !important;
                }
                
            """
            
            self.inner_body += icon
            self.inner_body += icon_style.to_string()
        
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
            for service_item in self.kwargs.get("services", []):
                # Create and add info to service card
                service_card = ServiceCard(**service_item)
                
                # Add service card
                self.add_child(service_card)
