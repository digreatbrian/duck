"""
HTML components template tags.

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
import ast

from typing import Any, List, Dict, Tuple
from duck.html.components import HtmlComponent, HtmlComponentError
from duck.template.templatetags import TemplateTag
from duck.utils.safemarkup import mark_safe


class HtmlComponentTemplateTag(TemplateTag):
    """
    HtmlComponentTemplateTag class.

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

    def __init__(
        self,
        component_name: str,
        component_cls: HtmlComponent,
    ):
        if not issubclass(component_cls, HtmlComponent):
            raise HtmlComponentError(
                f"Cannot create Html Component Tag: Argument component_cls should be a subclass of HtmlComponent not {component_cls}"
            )
        self.component_name = component_name
        self.component_cls = component_cls
        super().__init__(
            component_name,
           self.component_cls,
           takes_context=True,
       )
       
    def register_in_django(self, library):
        """
        Register this tag in a Django template library.

        Args:
            library: The Django template library to register the tag with.
        """
        from django import template
        
        root_tag = self
        
        class HtmlComponentNode(template.Node):
            def __init__(self, nodelist):
                self.nodelist = nodelist
                
            def render(self, context):
                # Resolve and evaluate the dictionaries
                content = self.nodelist.render(context)
               
                # Convert content to appropriate data type.
                args, kwargs = self.parse_args_kwargs(content)
                kwargs["context"] = context # set context
                
                try:
                    # return the MarkupSafe string
                    return mark_safe(root_tag.component_cls(*args, **kwargs).to_string())
                except Exception as e:
                    raise HtmlComponentError(f"Error invoking html component '{root_tag.tagname}': {e} ")

            def parse_args_kwargs(self, content: str) -> Tuple[List[Any], Dict[str, Any]]:
                """
                Parses a string of arguments and keyword arguments and returns them as a tuple of (args, kwargs).
                
                Args:
                    content (str): The string representation of the arguments and keyword arguments.
                
                Returns:
                    Tuple[List[Any], Dict[str, Any]]: A tuple containing positional arguments in a list and keyword arguments in a dictionary.
                """
                def accept_all(*args, **kwargs):
                    """Accept and returns all arguments and keyword arguments."""
                    return args, kwargs
                
                # Initialize empty args list and kwargs dictionary
                args = []
                kwargs = {}

                if not content.strip():
                    return args, kwargs

                try:
                    content = content.strip()
                    
                    # Evaluate the content as a tuple
                    content = f"accept_all({content})"
                    
                    evaluated_content = eval(content, {"accept_all": accept_all, "__builtins__": {}}, {})
                    
                    for item in evaluated_content:
                        # Handle keyword arguments (dictionaries)
                        if isinstance(item, dict):
                            kwargs.update(item)
                        # Handle positional arguments (lists or single values)
                        else:
                            args.append(item)
                            
                except SyntaxError as e:
                    line_number = content.count('\n', 0, e.offset) + 1
                    raise ValueError(
                        f"Syntax error in content '{content}' for component '{root_tag.component_name}' at line {line_number}: {e}"
                    ) from e
                
                except ValueError as e:
                    line_number = content.count('\n', 0, e.offset) + 1
                    raise ValueError(
                        f"Value error in content '{content}' for component '{root_tag.component_name}' at line {line_number}: {e}"
                    ) from e
                
                except Exception as e:
                    raise ValueError(
                        f"Unexpected error whilst parsing content '{content}' for component '{root_tag.component_name}': {e}"
                    ) from e
                return args, kwargs
            
        @library.tag(name=self.component_name)
        def django_tag_wrapper(parser, token):
            try:
                tokens = token.split_contents()
                tag_name = tokens.pop(0)  # Remove the tag name
                
                # Parse the block content
                nodelist = parser.parse((f"end{tag_name}",))
                parser.delete_first_token()
                return HtmlComponentNode(nodelist)
            except Exception as e:
                raise template.TemplateSyntaxError(f"Error parsing html component tag: {e}")
            
    def register_in_jinja2(self, environment):
        """
        Register this tag in a Jinja2 environment.

        Args:
            environment: The Jinja2 environment to register the tag with.
        """
        @mark_safe
        def jinja2_tag_wrapper(*args, **kwargs):
                return self.component_cls(*args, **kwargs).to_string()
        environment.globals[self.tagname] = jinja2_tag_wrapper
