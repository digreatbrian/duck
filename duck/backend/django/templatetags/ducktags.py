"""
Module for registering tags or filters that were initially registered by `Duck`, making them readily available in `Django` as well.

``` {warning}
Do not delete or edit this file unless you understand its purpose and functionality.
```

Notes:
- By default, in all TemplateResponses, The tags registered here will be available for use as builtins.
- In Django Sided Templates (Templates rendered by using django.shortcuts.render), for you to use the template filters and tags defined within Duck,

You need to load the duck tags by using this line:

```django
{% load ducktags %}
```
"""
from functools import partial
from typing import Dict, Any
from django import template
from duck.settings.loaded import ALL_TEMPLATETAGS # include html component tags, filters and all other tags


register = template.Library()


def register_duck_templatetags(library):
    """
    Registers all template tags and filters created within Duck.
    """
    for tag_or_filter in ALL_TEMPLATETAGS:
        tag_or_filter.register_in_django(library)


register_duck_templatetags(register) # Register all template tags and filters created within Duck.
