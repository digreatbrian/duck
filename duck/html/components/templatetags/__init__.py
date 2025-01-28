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
                args, kwargs = self.resolve_content(content)
                try:
                    # return the MarkupSafe string
                    return mark_safe(root_tag.component_cls(*args, **kwargs).to_string())
                except Exception as e:
                    raise HtmlComponentError(f"Error invoking html component '{root_tag.tagname}': {e} ")
            
            def resolve_content(self, content: str) -> Tuple[List[str], Dict[str, Any]]:
                """
                Resolves the content/string and converts it to appropriate data type.
                
                Returns:
                    Tuple[List[str], Dict[str, Any]]:
                        A tuple containing positional arguments in a 
                        list and keyword arguments in a dictionary.
                """
                # Expected content => properties = { 1: "Hello props" }, style = { "Hello" }
                args = []
                kwargs = {}
                try:
                    for line in content.split(','):
                        line = line.strip()
                        if "=" not in line:
                            args.append(ast.literal_eval(line))
                        else:
                            key, value = line.split('=', 1)
                            kwargs[key.strip()] = ast.literal_eval(value) # add keyword arg to kwargs
                except Exception as e:
                    raise template.TemplateSyntaxError(
                        f"Encountered an error whilst converting content for html component tag '{root_tag.tagname}' to appropriate data type: {e}"
                    )
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
            except Exception:
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
