"""
Module for HTTP template responses.

Do not mix DjangoTemplateResponse and Jinja2TemplateResponse if the templates being used extend from each other. This is to prevent template syntax errors between the two template backends.

Example:
    # templates/base.html
    # Jinja2 template
    {{ custom_tag("input") }}
    
    # templates/home.html
    # Django template
    {% extends 'base.html' %}
    
This may raise a Django TemplateSyntaxError if home.html is being rendered, as the file it tries to extend from contains invalid syntax for Django but valid syntax for Jinja2. The error will result from the Jinja2 form: {{ custom_tag("input") }}, which is expected to be {% custom_tag "input" %} by Django.
"""

from duck.http.response import DjangoTemplateResponse, Jinja2TemplateResponse

__all__ = ["Jinja2TemplateResponse", "DjangoTemplateResponse"]
