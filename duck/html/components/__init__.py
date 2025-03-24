"""
This module defines HTML components or elements that can be inserted into HTML pages.

These components are applied only if a templating engine is in use, such as Jinja2 or Django Template Engine.

Example Usage:
    # Jinja2 Template
    {{ Button(
         properties={
             "value": "Hello world",
              "id": "btn"
          },
          style={
              "background-color": "red",
               "color": "white",
            },
            optional_argument="Some value",
          )
    }}
    
    # Django Template
    {% Button %}
         properties={
             "id": "btn",
             "value": "Hello world"
          },
          style={
               "background-color": "blue",
                "color": "white"
           },
           optional_argument="Some value"
    {% endButton %}
"""

import re

from typing import Dict, List, Optional


def quote(html: str, element: str = 'span'):
    """
    Returns an html component quoting the provided html as its body.
    
    Args:
        html (str): The html to quote, to set as the new html component body.
        element (str): Element to quote with, Defaults to span.
    
    Returns:
        InnerHtmlComponent: The html component with provided html as its body.
    """
    return InnerHtmlComponent(inner_body=html, element=element)


class PropertiesStore(dict):
    """
    A dictionary subclass to store properties for HTML components, with certain restrictions.
    """

    def __setitem__(self, key, value):
        """
        Sets the value for the given key if the key is allowed.

        Args:
            key (str): The key to set the value for. Must be a string.
            value (str): The value to set. Must be a string.

        Raises:
            KeyError: If the key is 'style', as it is not allowed to be set.
            AssertionError: If the key or value is not a string.
        """
        if key == "style":
            raise KeyError(
                f"Property 'style' is not allowed to be set in {self.__class__.__name__}")
        assert isinstance(
            key, str), "Keys for PropertiesStore should be strings"
        assert isinstance(
            value, str), "Values for PropertiesStore should be strings"
        super().__setitem__(key.strip().lower(), value)

    def __repr__(self):
        """
        Returns a string representation of PropertiesStore.

        Returns:
            str: String representation of the PropertiesStore.
        """
        return f"<{self.__class__.__name__} {super().__repr__()}>"
        
    def setdefaults(self, data: Dict):
        """
        Method setdefault on multiple items
        """
        for key, value in data.items():
            self.setdefault(key, value)


class HtmlComponentError(Exception):
    """
    Exception raised for errors in the HtmlComponent.
    """


class NoParentError(Exception):
    """
    Exception raised for errors when an html component has no parent.
    """


class HtmlComponent:
    """
    Base class for HTML components.
    """

    def __init__(
        self,
        element: Optional[str] = None,
        accept_inner_body: bool = False,
        inner_body: str = None,
        properties: Dict[str, str] = {},
        style: Dict[str, str] = {},
        **kwargs,
    ):
        """
        Initialize an HTML component.

        Args:
            element (Optional[str]): The HTML element tag name (e.g., textarea, input, button). Can be None, but make sure element is returned by get_element method.
            accept_inner_body (bool): Whether the HTML component accepts an inner body (e.g., <strong>inner-body-here</strong>).
            inner_body (str, optional): Inner body to add to the HTML component. Defaults to None.
            properties (dict, optional): Dictionary for properties to initialize the component with.
            style (dict, optional): Dictionary for style to initialize the component with.
            **kwargs: Extra keyword arguments
        
        Raises:
            HtmlComponentError: If 'element' is not a string or 'inner_body' is set but 'accept_inner_body' is False.
        """
        
        element = element or self.get_element()
        
        if not isinstance(element, str):
            raise HtmlComponentError(
                f"Argument 'element' should be a valid string representing the HTML element tag name not \"{element}\": {type(element)}."
            )
            
        if not re.findall(r"\b[a-zA-Z0-9]+\b", element):
            raise HtmlComponentError(
                f"Argument 'element' is has invalid format, change the elemebt to something else."
            )

        if inner_body and not accept_inner_body:
            raise HtmlComponentError(
                "Argument 'inner_body' is set yet 'accept_inner_body' is False."
            )
        
        # Set roperties and style for the HTML element/component
        self.__properties = PropertiesStore() # Basic properties
        self.__style = PropertiesStore()  # Properties for CSS styling
        self.__parent = None
        
        self.element = element
        self.accept_inner_body = accept_inner_body
        self.inner_body = inner_body
        
        properties = properties or {}
        style = style or {}
        
        assert isinstance(properties, dict) == True, f"Properties for the Html component must be a dictionary not '{type(properties)}' "
        assert isinstance(style, dict) == True, f"Style for the Html component must be a dictionary not '{type(properties)}'"
        
        # add some properties and style
        self.__properties.update(properties)
        self.__style.update(style)
        
        self.kwargs = kwargs
        self.on_create()

    @property
    def properties(self):
        """
        Returns the properties store for the HTML component.

        Returns:
            PropertiesStore: The properties store for the HTML component.
        """
        return self.__properties

    @property
    def style(self):
        """
        Returns the style store for the HTML component.

        Returns:
            PropertiesStore: The style store for the HTML component.
        """
        return self.__style

    @property
    def parent(self):
        """
        Returns the parent for the html component. This is only resolved if this html component has been added to some html component children.
        """
        if not self.__parent:
            raise NoParentError("Html component has not been added to any parent component.")
        return self.__parent
        
    @parent.setter
    def parent(self, parent):
        """
        Sets the parent for the html component.
        """
        self.__parent = parent
        
    def get_element(self):
        """
        Fallback method to retrieve the html element tag.
        """
        raise NotImplementedError(f"Method `get_element` is not implemented yet the element argument is empty or None. This is a fallback method.")
    
    def on_create(self):
        """
        Called on component creation or initialization
        """
    
    def get_inner_css_string(self):
        """
        Retrieves the CSS string for the styles set on the HTML component.

        Returns:
            str: The CSS string for the styles.
        """
        css = ""
        for style, value in self.style.items():
            css += f"{style}: {value}; "
        return css.strip().rstrip(";")

    def get_inner_properties_string(self):
        """
        Retrieves the HTML element properties string for the properties set on the HTML component.

        Returns:
            str: The HTML element properties string.
        """
        properties = ""
        for attr, value in self.properties.items():
            properties += f'{attr}="{value}" '
        return properties.strip()

    def to_string(self, add_style: bool = True):
        """
        Returns the string representation of the HTML component.

        Args:
            add_style (bool, optional): Whether to add CSS style to the HTML element. Defaults to True.

        Returns:
            str: The string representation of the HTML component.
        """
        inner_prop_string = self.get_inner_properties_string()
        elem_string = f"<{self.element}"
        if inner_prop_string:
            elem_string += f" {inner_prop_string}"

        if add_style:
            css = self.get_inner_css_string()
            if css:
                elem_string += f' style="{css}"'

        elem_string += ">"
        if self.accept_inner_body:
            elem_string += f'{self.inner_body or ""}</{self.element}>'
        return elem_string

    def __str__(self) -> str:
        """
        Returns:
            str: A string representation of the Html Element witn style and properties.
        """
        return self.to_string()

    def __repr__(self):
        return f"<{self.__class__.__name__} element='{self.element}'>"


class NoInnerHtmlComponent(HtmlComponent):
    """
    This is the HTML component with no Inner Body.

    Form:
        <mytag> or <mytag/>

        Example:
            <input>
            <textarea>

    Notes:
        - The html components that fall in this category are usually HTML Input elements.
    """

    def __init__(
        self,
        element: Optional[str] = None,
        properties: Dict[str, str] = {},
        style: Dict[str, str] = {},
        **kwargs,
    ):
        super().__init__(
            element,
            accept_inner_body=False,
            properties=properties,
            style=style,
            **kwargs,
        )


class InnerHtmlComponent(HtmlComponent):
    """
    This is the HTML component with Inner Body presence.

    Form:
        <mytag>Text here</mytag>

        Example:
            <p>Text here</p>
            <h2>Text here</h2>
            <ol>List elements here</ol>

    Notes:
        - The html components that fall in this category are usually basic HTML elements.
    """

    def __init__(
        self,
        element: Optional[str] = None,
        properties: Dict[str, str] = {},
        style: Dict[str, str] = {},
        inner_body: str = "",
        **kwargs,
    ):
        self.children = [] # initialize the children list
        
        super().__init__(
            element,
            accept_inner_body=True,
            inner_body=inner_body,
            properties=properties,
            style=style,
            **kwargs,
        )
        
    def add_child(self, child: HtmlComponent):
        """
        Adds a child component to this HTML component.

        Args:
            child (HtmlComponent): The child component to add.
        """
        child.parent = self
        self.children.append(child)

    def add_children(self, children: List[HtmlComponent]):
        """
        Adds multiple child components to this HTML component.

        Args:
            children (list): The list of child components to add.
        """
        for child in children:
            self.add_child(child)
    
    def remove_child(self, child: HtmlComponent):
        """
        Removes a child component from this HTML component.

        Args:
            child (HtmlComponent): The child component to remove.
        """
        if child in self.children:
            self.children.remove(child)
        else:
            raise ValueError(f"Child component {child} not found in children list.")
    
    def to_string(self, add_style: bool = True):
        """
        Returns the string representation of the HTML component.

        Args:
            add_style (bool, optional): Whether to add CSS style to the HTML element. Defaults to True.

        Returns:
            str: The string representation of the HTML component.
        """
        inner_prop_string = self.get_inner_properties_string()
        elem_string = f"<{self.element}"
        
        if inner_prop_string:
            elem_string += f" {inner_prop_string}"
        
        if add_style:
            css = self.get_inner_css_string()
            if css:
                elem_string += f' style="{css}"'

        elem_string += ">"
        
        if self.accept_inner_body:
            elem_string += f'{self.inner_body or ""}'
        
        # Add child components
        for child in self.children:
            elem_string += child.to_string(add_style)

        elem_string += f'</{self.element}>'
        return elem_string


class Theme:
    """
    Default Duck theme.
    """
    primary_color = "#4B4E75"  # Dark Blue
    secondary_color = "#A6B48B"  # Soft Green
    background_color = "#FFFFFF"  # White
    text_color = "#333333"  # Dark Grey for readability
    font_family = "Arial, sans-serif"
    border_radius = "15px"
    padding = "10px"
    button_style = {
        "background": primary_color,
        "text_color": "#FFFFFF",
        "border_radius": "5px",
        "padding": "10px 20px"
    }
    normal_font_size = "16px"
