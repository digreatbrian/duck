from duck.html.components import InnerHtmlComponent
from duck.html.components.button import FlatButton
from duck.etc.templatetags import static

from theme import Theme
from .container import FlexContainer
from .image import Image


class HeroLeftContent(FlexContainer):
    def on_create(self):
        super().on_create()
        self.style["flex-direction"] = "column"
        self.style['width'] = "50%"
        self.properties["class"] = "text-color-primary"
        
        heading = self.kwargs.get('heading', '')
        subheading = self.kwargs.get('subheading', '')
        
        # Add heading and subheading
        self.inner_body += f'<h1 id="hero-heading" class="hero-heading">{heading}</h1>'
        self.inner_body += f'<p id="hero-subheading" class="hero-subheading">{subheading}</p>'
        
        # Add cta btn
        cta_btn = FlatButton()
        cta_btn.inner_body = "Get consultation"
        cta_btn.style["background-color"] = "rgba(100, 100, 100, .25)"
        cta_btn.style["color"] = "#ccc"
        cta_btn.style["margin-top"] = "5px"
        cta_btn.style["border_radius"] = Theme.border_radius
        cta_btn.style["font-size"] = "1.2rem"
        cta_btn.style["border"] = ".25px solid #ccc"
        
        self.inner_body += cta_btn.to_string()


class HeroRightContent(FlexContainer):
    def on_create(self):
        super().on_create()
        self.style["flex-direction"] = "column"
        self.style["background-color"] = "rgba(100, 100, 100, .25)"
        self.style["min-height"] = "50vh"
        self.style["min-width"] = "30%"
        self.style["border-radius"] = Theme.border_radius
        self.properties["class"] = "text-color-primary"
        
        # Create and add image and placeholder to image container
        image_container = FlexContainer()
        image_container.style["flex-direction"] = "column"
        image_container.style["position"] = "absolute"
        image_container.style["right"] = "0px"
        
        # Add image to image container
        image = Image(source=static('images/founder.png'))
        image.style["object-fit"] = "contain"
        image_container.add_child(image)
        
        # Add placeholder to image container
        placeholder = FlexContainer()
        placeholder.style["min-height"] = "100px"
        placeholder.style["min-width"] = "30px"
        placeholder.style["justify-content"] = "center"
        placeholder.style["align-items"] = "center"
        placeholder.style["backdrop-filter"] = "blur(50px)"
        image_container.add_child(placeholder)
        
        # Add cta btn to placeholder
        cta_btn = FlatButton(inner_body="Get free Quote")
        cta_btn.style["color"] = "#ccc"
        cta_btn.style["width"] = "80%"
        cta_btn.style["background-color"] = "transparent"
        cta_btn.style["font-size"] = "1.5rem"
        cta_btn.style["border"] = "1px solid #ccc"
        placeholder.add_child(cta_btn)
        
        # Add image container
        self.add_child(image_container)


class HeroContent(FlexContainer):
    def on_create(self):
        super().on_create()
        self.properties["class"] = "hero-content"
        self.style["justify-content"] = "space-between"
        self.style["width"] = "98%"
        self.style["position"] = "absolute"
        self.style["padding"] = Theme.padding
        self.style["top"] = "25%"
        
        # Add Hero left content
        hero_left_content = HeroLeftContent(**self.kwargs)
        self.add_child(hero_left_content)
        
        # Add Hero right content
        hero_right_content = HeroRightContent(**self.kwargs)
        self.add_child(hero_right_content)


class HeroBackground(FlexContainer):
    def on_create(self):
        super().on_create()
        self.properties["class"] = "hero-background"
        self.style["flex-direction"] = "column"
        

class Hero(FlexContainer):
    """
    HTML Hero component.
    """
    def on_create(self):
        super().on_create()
        self.style["flex-direction"] = "column"
        self.style["width"] = "100%"
        self.style["height"] = "100vh"
        self.style["padding"] = "15px 15px 30px 15px"
        self.properties["class"] = "hero display-flex justify-content-center"
        
        hero_background = HeroBackground(inner_body=self.kwargs.get('background_html', ''))
        self.add_child(hero_background)
        
        # Add Hero Content
        hero_content = HeroContent(**self.kwargs)
        self.add_child(hero_content)
