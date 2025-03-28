"""
Table of Contents HTML Component.

This module defines two components:
1. `TableOfContentsSection` - Represents a content section with a heading and body.
2. `TableOfContents` - Generates a navigable table of contents.

Each `TableOfContentsSection` is added to the `TableOfContents` component, which 
automatically creates a clickable list of links for navigation.
"""

from duck.html.components.container import FlexContainer
from duck.html.components import quote
from duck.utils.slug import slugify


class TableOfContentsSection(FlexContainer):
    """
    Represents a section in the Table of Contents.

    Each section consists of a heading (anchor link target) and body content.

    Args:
    - `heading` (str): The heading of the section, which will be linked in the Table of Contents.
    - `body` (str): The main content of the section, which can be plain text or HTML.
    """
    
    def on_create(self):
        super().on_create()
        self.style["flex-direction"] = "column"
        self.style["margin-top"] = "10px"
        self.properties["class"] = "toc-section"
        
        self.heading = None
        self.body = None

        # Add heading if provided
        if "heading" in self.kwargs:
            heading_text = self.kwargs.get("heading") or ""
            self.heading = quote(heading_text, "h1")
            self.heading.properties["class"] = "toc-heading"
            self.heading.properties["id"] = slugify(heading_text)
            self.add_child(self.heading)
        
        # Add body content if provided
        if "body" in self.kwargs:
            body_content = self.kwargs.get("body") or ""
            self.body = quote(body_content, "div")
            self.body.style["display"] = "flex"
            self.body.style["flex-direction"] = "column"
            self.body.properties["class"] = "toc-body"
            self.add_child(self.body)


class TableOfContents(FlexContainer):
    """
    Table of Contents Component.

    This component generates a navigable list of links to `TableOfContentsSection` instances.

    Args:
        title (str): The title displayed at the top of the Table of Contents. Defaults to "Table of Contents".
    """

    def on_create(self):
        super().on_create()
        self.style["flex-direction"] = "column"
        self.style["gap"] = "3px"
        self.properties["class"] = "table-of-contents"

        # Set title
        title_text = self.kwargs.get("title", "Table of Contents")
        self.title = quote(title_text, "h1")
        self.title.properties["class"] = "toc-title"

        # Create list container for quick navigation links
        self.list_container = quote("", "ul")
        self.list_container.properties["class"] = "toc-list"

        # Add title and list container to the component
        super().add_child(self.title)
        super().add_child(self.list_container)

    def add_child(self, child: TableOfContentsSection, list_style: str = "circle"):
         """
         Adds a `TableOfContentsSection` to the Table of Contents.

        This method also creates a clickable link for the section heading.

         Args:
            section (TableOfContentsSection): The section to add.
            list_style (str): The CSS list-style type for the navigation items. Defaults to "circle".
         """
         self.add_section(child, list_style)
        
    def add_section(self, section: TableOfContentsSection, list_style: str = "circle"):
        """
        Adds a `TableOfContentsSection` to the Table of Contents.

        This method also creates a clickable link for the section heading.

        Args:
            section (TableOfContentsSection): The section to add.
            list_style (str): The CSS list-style type for the navigation items. Defaults to "circle".
        """
        assert isinstance(section, TableOfContentsSection), "Only a TableOfContentsSection component is allowed"

        if section.heading:
            heading_text = section.heading.inner_body
            heading_link = quote(heading_text, "a")
            heading_link.style["text-decoration"] = "none"
            heading_link.properties["href"] = f"#{section.heading.properties.get('id', '')}"

            list_item = quote(heading_link.to_string(), "li")
            list_item.style["list-style"] = list_style
            self.list_container.add_child(list_item)

        # Add the section to the Table of Contents
        super().add_child(section)
