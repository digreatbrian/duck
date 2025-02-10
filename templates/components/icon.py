from .link import Link


class IconLink(Link):
    def on_create(self):
        super().on_create()
        self.style["color"] = "#ccc"
