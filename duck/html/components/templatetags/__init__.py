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
           takes_context=False,
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
                
                # Normalize content to avoid syntax errors
                content = self._normalize_content(content)
                
                # Convert content to appropriate data type.
                args, kwargs = self.parse_args_kwargs(content)
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
                    content = content.strip().replace("\n", "").replace("\r", "").replace("\t", "").replace(" ", "")
                    
                    # Evaluate the content as a tuple
                    content = f"accept_all({content})"
                    
                    evaluated_content = eval(content, {"accept_all": accept_all, "__builtins__": None}, {})
                    
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
            
            def _normalize_content(self, content: str) -> str:
                """
                Cleans up and normalizes content to ensure it is valid for parsing with ast.literal_eval.
                Behaves like most formatters to handle nested and indented structures.
                """
                # Step 1: Split lines and strip unnecessary spaces
                lines = content.splitlines()
                stripped_lines = [line.strip() for line in lines if line.strip()]  # Remove blank lines
            
                # Step 2: Join lines into a single string
                joined_content = " ".join(stripped_lines)
            
                # Step 3: Fix common issues
                # Remove trailing commas in dicts and lists
                normalized_content = re.sub(r",\s*}", "}", joined_content)  # Remove trailing commas in dicts
                normalized_content = re.sub(r",\s*]", "]", normalized_content)  # Remove trailing commas in lists
            
                # Ensure consistent spacing around colons and commas
                normalized_content = re.sub(r"\s*:\s*", ": ", normalized_content)  # Space after colons
                normalized_content = re.sub(r"\s*,\s*", ", ", normalized_content)  # Space after commas
            
                return normalized_content.strip()
            
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
