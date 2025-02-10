from duck.html.components import InnerHtmlComponent
from duck.etc.templatetags import static

from theme import Theme
from .container import FlexContainer, Container
from .card import Card
from .image import Image


class Carousel(Container):
    def on_create(self):
        super().on_create()
        self.properties["class"] = "carousel slide"
        self.properties["data-ride"] = "carousel"
        self.properties["data-interval"] = "3000"
        
        carousel_inner = Container()
        carousel_inner.properties["class"] = 'carousel-inner'
        
        if "items" in self.kwargs:
            for item in self.kwargs.get('items', []):
                carousel_inner.add_child(item)
       
        self.add_child(carousel_inner)


class CarouselItem(Container):
    def on_create(self):
        super().on_create()
        self.properties["class"] = "carousel-item"
        self.style["min-height"] = "300px"
        self.style["backdrop-filter"] = "blur(100px)"
        self.style["background-color"] = "transparent"
        self.style["border-radius"] = Theme.border_radius
        self.style["border"] = "1px solid #ccc"
        self.style["padding"] = Theme.padding
        
        if "active" in self.kwargs:
            if self.kwargs.get('active'):
                self.properties["class"] += " active"
       
        item_card = Card()
        item_card.style["flex-direction"] = "column"
        item_card.style["justify-content"] = "center"
        item_card.style["align-items"] = "center"
        item_card.style["height"] = "100%"
        item_card.style["gap"] = "10px"
        
        if "image_source" in self.kwargs:
            image_source = self.kwargs.get('image_source', '')
            image = Image(source=image_source)
            image.style["width"] = "250px"
            image.style["height"] = "250px"
            image.style["border-radius"] = Theme.border_radius
            image.properties["class"] = "about-carousel-item-image"
            item_card.inner_body += image.to_string()
        
        if "heading" in self.kwargs:
            heading = self.kwargs.get('heading', '')
            item_card.inner_body += f"<h3 class='about-carousel-item-heading'>{heading}</h3>"
        
        if "subheading" in self.kwargs:
            subheading = self.kwargs.get('subheading', '')
            item_card.inner_body += f"<p class='about-carousel-item-subheading'>{subheading}</p>"
        
        self.add_child(item_card)


class TopContent(FlexContainer):
    def on_create(self):
        super().on_create()
        self.style["flex-direction"] = "column"
        # Add heading
        self.inner_body += "<h1>About Us</h1>"
        
        # Add About us content
        intro = """
        At Yannick Consultancy, we help businesses thrive through tailored solutions, expert advice, and innovative strategies.
        Founded in 2025, our consultancy firm partners with clients to unlock growth, improve efficiency, and achieve lasting success."""
        self.inner_body += f"<p id='about-intro'>{intro}</p>"


class BottomContent(FlexContainer):
    def on_create(self):
        super().on_create()
        self.style["flex-direction"] = "column"
        self.style["gap"] = "10px"
        
        # Add heading
        self.inner_body += "<h2>Why choose us</h2>"
        
        # Add carousel and carousel items 
        first_item = CarouselItem(
            active=True,
            heading="Tailored Solutions",
            subheading="Strategies designed specifically for your business",
            image_source=static('images/puzzle-pieces.png'))
        
        second_item = CarouselItem(
            heading="Results-Driven",
            subheading="We focus on delivering measurable outcomes",
            image_source=static('images/rocket.png'))
        
        carousel_items = [
            first_item,
            second_item,
        ]
        carousel = Carousel(items=carousel_items)
        self.inner_body += carousel.to_string()
        
        if "extra_content" in self.kwargs:
            self.inner_body += self.kwargs.get("extra_content", '')
        

class AboutUs(FlexContainer):
    def on_create(self):
        super().on_create()
        self.style["min-width"] = "80%"
        self.style["min-height"] = "200px"
        self.style["border"] = "1px solid #ccc"
        self.style['border-radius'] = Theme.border_radius
        self.style["padding"] = "20px"
        self.style["margin-top"] = "0px"
        self.style["color"] = "#ccc"
        self.style["backdrop-filter"] = "blur(20px)"
        self.style["font-size"] = "1.8rem"
        self.style["background-size"] = "cover"
        self.style["background-repeat"] = "no-repeat"
        self.style["flex-direction"] = "column"
        self.style["gap"] = "15px"
        self.properties["id"] = "about-us"
        
        # Add top content
        top_content = TopContent(**self.kwargs)
        self.add_child(top_content)
        
        # Add bottom content
        bottom_content = BottomContent(**self.kwargs)
        self.add_child(bottom_content)
        