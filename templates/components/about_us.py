from duck.html.components import InnerHtmlComponent
from duck.etc.templatetags import static

from theme import Theme
from .container import FlexContainer
from .image import Image


class Carousel(FlexContainer):
    def on_create(self):
        super().on_create()
        self.properties["class"] = "carousel slide"
        self.properties["data-bs-ride"] = "carousel"
        if "items" in self.kwargs

class LeftContent(FlexContainer):
    def on_create(self):
        super().on_create()
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
        
        # Add heading
        self.inner_body += "<h2>Why choose us</h2>"
        
        # Add corousel
        corousel = FlexContainer()
        

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
        self.style["flex-direction"] = "row"
        self.style["gap"] = "5px"
        self.properties["id"] = "about-us"
        
        