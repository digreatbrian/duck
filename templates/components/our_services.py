from duck.etc.templatetags import static

from theme import Theme

from .container import FlexContainer
from .style import Style


class OurServicesStyle(Style):
    def on_create(self):
        super().on_create()
        self.inner_body += """
            .nav-hero-section {
                background-image: url({url}) !important;
            }
            
            .service-cards {
                justify-content: center !important;
                gap: 10px !important;
            }
            
            .service-card {
                width: 45%;
            }
        """.replace('{url}', static('images/bg-black-gradient.png'))


class OurServices(FlexContainer):
    def on_create(self):
        super().on_create()
        self.style["min-width"] = "80%"
        self.style["min-height"] = "200px"
        self.style["border"] = "1px solid #ccc"
        self.style['border-radius'] = Theme.border_radius
        self.style["padding"] = "20px"
        self.style["margin-top"] = "10px"
        self.style["color"] = "#ccc"
        self.style["backdrop-filter"] = "blur(20px)"
        self.style["background-size"] = "cover"
        self.style["background-repeat"] = "no-repeat"
        self.style["flex-direction"] = "column"
        self.style["gap"] = "15px"
        self.style["align-items"] = "center"
        self.properties["id"] = "our-services"
