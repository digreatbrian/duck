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
        self.style["height"] = "300px"
        self.style["backdrop-filter"] = "blur(100px)"
        self.style["background-color"] = "transparent"
        self.style["border-radius"] = Theme.border_radius
        self.style["border"] = "1px solid #ccc"
        
        if "active" in self.kwargs:
            if self.kwargs.get('active'):
                self.properties["class"] += " active"


class LeftContent(FlexContainer):
    def on_create(self):
        super().on_create()
        self.style["flex-direction"] = "column"
        # Add heading
        self.inner_body += "<h2>About Us</h2>"
        
        # Add About us content
        intro = """
        At Yannick Consultancy, we help businesses thrive through tailored solutions, expert advice, and innovative strategies.
        Founded in 2025, our consultancy firm partners with clients to unlock growth, improve efficiency, and achieve lasting success."""
        self.inner_body += f"<p id='about-intro'>{intro}</p>"


class RightContent(FlexContainer):
    def on_create(self):
        super().on_create()
        self.style["flex-direction"] = "column"
        
        # Add heading
        self.inner_body += "<h2>Why choose us</h2>"
        
        # Add carousel and carousel items 
        first_item = CarouselItem(active=True,)
        first_item_card = Card()
        first_item_card.style["flex-direction"] = "column"
        first_item_card.style["justify-content"] = "center"
        first_item_card.style["align-items"] = "center"
        first_item_card.style["height"] = "100%"
        first_item_card.inner_body = """
        <h3>Tailored Solutions</h3>
        <p>Strategies designed specifically for your business</p>"""
        first_item.add_child(first_item_card)
        
        # Second carousel item
        second_item = CarouselItem()
        second_item_card = Card()
        second_item_card.style["flex-direction"] = "column"
        second_item_card.style["justify-content"] = "center"
        second_item_card.style["align-items"] = "center"
        second_item_card.style["height"] = "100%"
        second_item_card.inner_body = """
        <h3>Results-Driven</h3>
        <p>We focus on delivering measurable outcomes</p>"""
        second_item.add_child(second_item_card)
        
        carousel_items = [
            first_item,
            second_item,
        ]
        carousel = Carousel(items=carousel_items)
        self.add_child(carousel)
        

class AboutUs(FlexContainer):
    def on_create(self):
        super().on_create()
        self.style["min-width"] = "80%"
        self.style["min-height"] = "200px"
        self.style["border"] = "1px solid #ccc"
        self.style['border-radius'] = Theme.border_radius
        self.style["padding"] = Theme.padding
        self.style["margin-top"] = "0px"
        self.style["background-image"] = f'url({static("images/bg-orange-purple-gradient.png")})'
        self.style["flex-wrap"] = "wrap"
        self.style["text-wrap"] = "break-word"
        self.style["color"] = "var(--secondary-color)"
        self.style["backdrop-filter"] = "blur(20px)"
        self.style["font-size"] = "1.8rem"
        self.style["background-size"] = "cover"
        self.style["background-repeat"] = "no-repeat"
        self.style["flex-direction"] = "column"
        self.style["gap"] = "5px"
        self.properties["id"] = "about-us"
        
        # Add left content
        left_content = LeftContent()
        self.add_child(left_content)
        
        # Add right content
        right_content = RightContent()
        self.add_child(right_content)
        