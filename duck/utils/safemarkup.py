"""
Module for creating safe strings compatible with both Jinja2 and Django template engines.

This module provides a utility class `SafeMarkup` that subclasses both `markupsafe.Markup`
and Django's `SafeString` classes. This ensures that strings marked as safe using this 
class will be considered safe in both Jinja2 and Django templates. 

Additionally, the module includes an example usage of the `MarkupSafeString` class to demonstrate 
how to create and use safe strings in both template engines.

The function `mark_safe` can also be used to mark strings safe as a decorator to the function which returns a string or to a mere string.

Usage Example:

```py
safe_string = mark_safe("<h1>Hello world</h1>")

# or using as a decorator
@mark_safe
def my_func():
    return "<h2>Hello world</h2>"
```
"""

from django.utils.safestring import SafeString
from markupsafe import Markup


class MarkupSafeString(SafeString, Markup):
    """
    A class that subclasses both `markupsafe.Markup` and Django's SafeString.

    This class ensures that strings marked as safe using this class will be
    considered safe in both Jinja2 and Django template engines.

    Args:
        value (str): The string to mark as safe.

    Example Usage:
    
    ```py
    safe_string = MarkupSafeString('<strong>bold</strong>')
    # You can use the safe string in templates.
    ```
    """


def mark_safe(func_or_str) -> MarkupSafeString:
    """
    Decorator and function to mark string as safe for inserting in html templates

    Behavior:
    - Works well as a decorator with no arguments
    - If func provided is a string, then Markup instance of the func is returned.
    """
    if isinstance(func_or_str, str):
        return MarkupSafeString(func_or_str)

    def wrapper(*args, **kw):
        output = func_or_str(*args, **kw)  # obtained function returned data
        return MarkupSafeString(output)

    return wrapper
