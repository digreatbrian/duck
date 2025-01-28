"""
Module for creating safe strings compatible with both Jinja2 and Django template engines.

This module provides a utility class `SafeMarkup` that subclasses both `markupsafe.Markup`
and Django's `SafeString` classes. This ensures that strings marked as safe using this 
class will be considered safe in both Jinja2 and Django templates. 

Additionally, the module includes an example usage of the `MarkupSafeString` class to demonstrate 
how to create and use safe strings in both template engines.

The function `mark_safe` can also be used to mark strings safe as a decorator to the function which returns a string or to a mere string.

Example:
	
	safe_string = mark_safe("<h1>Hello worlf</h1>")
	
	# or
	
	@mark_safe
	def my_func():
		return "<h2>Hello world</h2>"


Usage Example:

    # Example usage for Jinja2
    from jinja2 import Template
    from duck.utils.safemarkup import MarkupSafeString

    safe_string = MarkupSafeString('<strong>bold</strong>')

    jinja_template = Template('{{ safe_string }}')
    jinja_rendered = jinja_template.render(safe_string=safe_string)
    print(jinja_rendered)  # Output: <strong>bold</strong>

    # Example usage for Django
    from django.template import Template as DjangoTemplate, Context
    from safemarkup import SafeMarkup

    safe_string = MarkupSafeString('<strong>bold</strong>')

    django_template = DjangoTemplate('{{ safe_string }}')
    django_context = Context({'safe_string': safe_string})
    django_rendered = django_template.render(django_context)
    print(django_rendered)  # Output: <strong>bold</strong>
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
        safe_string = MarkupSafeString('<strong>bold</strong>')

        # Safe for Jinja2
        jinja_template = Template('{{ safe_string }}')
        jinja_rendered = jinja_template.render(safe_string=safe_string)
        print(jinja_rendered)  # Output: <strong>bold</strong>

        # Safe for Django
        from django.template import Template as DjangoTemplate, Context
        django_template = DjangoTemplate('{{ safe_string }}')
        django_context = Context({'safe_string': safe_string})
        django_rendered = django_template.render(django_context)
        print(django_rendered)  # Output: <strong>bold</strong>
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
