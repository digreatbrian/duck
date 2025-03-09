"""
Video html component.
"""
from duck.html.components import InnerHtmlComponent


class Video(InnerHtmlComponent):
    """
    HTML Video component.
    
    Args:
        source (str): Video source url
        alt (str): Video alternative text
        width (str): Video width
        height (str): Video height
        autoplay (bool): Whether to autoplay video
        loop (bool): Whether to loop video
        muted (bool): Whether to mute video
        playsinline (bool): Whether to turn on playsinline
        
    """
    def get_element(self):
        return "video"
        
    def on_create(self):
        self.properties.setdefault("type", "video/mp4")
        
        if self.kwargs.get("source"):
            self.properties["src"] = self.kwargs.get("source", '')
        
        if self.kwargs.get("alt"):
            self.properties["alt"] = self.kwargs.get("alt", '')
        
        if self.kwargs.get("width"):
            self.properties["width"] = self.kwargs.get("width", '')
            
        if self.kwargs.get("height"):
            self.properties["height"] = self.kwargs.get("height", '')
        
        if self.kwargs.get("autoplay"):
            self.properties["autoplay"] = "true"
        
        if self.kwargs.get("loop"):
            self.properties["loop"] = "true"
            
        if self.kwargs.get("muted"):
            self.properties["muted"] = "true"
        
        if self.kwargs.get("playsinline"):
            self.properties["playsinline"] = "true"
