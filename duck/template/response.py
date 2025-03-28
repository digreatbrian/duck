"""
# HTTP Template Responses Module

This module handles HTTP template responses and provides guidance on using different template backends.

``` {important}
Avoid mixing `DjangoTemplateResponse` and `Jinja2TemplateResponse` when the templates extend from each other. Mixing these two can lead to syntax errors, as they have different template syntax rules.
```

## Common Error Scenario

This issue may result in a `Django TemplateSyntaxError` when rendering a template like `home.html`. If the template extends from a file that contains syntax valid in `Jinja2` but invalid in `Django`, the error occurs. 

For example, in Jinja2, the tag `{{ custom_tag("input") }}` is used, whereas in Django templates, the correct syntax would be `{% custom_tag "input" %}`.

To prevent such errors, ensure consistency between the template backends being used.
"""

from duck.http.response import DjangoTemplateResponse, Jinja2TemplateResponse

__all__ = ["Jinja2TemplateResponse", "DjangoTemplateResponse"]
