"""
Module for creating user custom template tags and filters.
"""

from collections import defaultdict
from typing import Callable

from jinja2 import nodes
from jinja2.ext import Extension

from duck.exceptions.all import SettingsError
from duck.utils.importer import import_module_once
from duck.utils.safemarkup import MarkupSafeString


class TemplateTagError(Exception):
    """Exception for errors related to the TemplateTag class."""


class TemplateFilterError(Exception):
    """Exception for errors related to the TemplateFilter class."""


class TemplateTag:
    """
    Base class for defining and registering template tags.

    This class provides a unified way to register template tags in templating 
    engines like Django or Jinja2. It supports callable tags, allowing flexible 
    logic to be associated with the tag.

    Usage:
        1. Define a callable function to handle the tag logic:
        
            def do_something(arg):
                # Perform some operations with the argument
                return f"Processed: {arg}"

        2. Register the callable as a template tag:
        
            tag = TemplateTag("my_tag", tagcallable=do_something)

    Supported Syntax:
        - Django: {% my_tag arg1 arg2 %}
        - Jinja2: {{ my_tag(arg1, arg2) }}
    """

    __all_tags = defaultdict(str)
    # Dictionary for all created tags

    def __init__(self,
                 tagname: str,
                 tagcallable: Callable,
                 takes_context: bool = False):
        self.tagname = tagname
        self.tagcallable = tagcallable
        self.takes_context = takes_context

        assert isinstance(
            tagname, str
        ), f"Argument 'tagname' should be an instance of string not {type(tagname)}"
        assert callable(
            tagcallable
        ), f"Argument 'tagcallable' should be a callable not {type(tagcallable)}"
        assert isinstance(
            takes_context, bool
        ), f"Argument 'takes_context' should be a boolean not {type(takes_context)}"

        if not self.__all_tags[tagname]:
            type(self).__all_tags[tagname] = self
        else:
            raise TemplateTagError(
                f"Repeated template tag '{tagname}', already exists")
    
    @classmethod
    def get_tag(cls, tagname: str):
        """
        Retreive a created Template Tag with provided name.

        Raises:
            TemplateTagError: If tag with provided name does'nt exist.
        """
        tag = cls.__all_tags.get(tagname)
        if not tag:
            raise TemplateTagError(
                f"Template Tag with name '{tagname}' was never created.")
        return tag
 
    def register_in_django(self, library):
        """
        Register this tag in a Django template library.

        Args:
            library: The Django template library to register the tag with.
        """
        if self.takes_context:
            @library.simple_tag(name=self.tagname, takes_context=self.takes_context)
            def django_tag_wrapper(context, *args, **kwargs):
                return self.tagcallable(context, *args, **kwargs)
        else:
            @library.simple_tag(name=self.tagname, takes_context=self.takes_context)
            def django_tag_wrapper(*args, **kwargs):
                return self.tagcallable(*args, **kwargs)
  
    def register_in_jinja2(self, environment):
        """
        Register this tag in a Jinja2 environment.

        Args:
            environment: The Jinja2 environment to register the tag with.
        """
        from jinja2 import pass_context
        
        if self.takes_context:
            @pass_context
            def jinja2_tag_wrapper(*args, **kwargs):
                return self.tagcallable(*args, **kwargs)
            environment.globals[self.tagname] = jinja2_tag_wrapper
        else:
            environment.globals[self.tagname] = self.tagcallable

    def __repr__(self):
        """
        Returns a string representation of the TemplateTag.

        Returns:
            str: String representation of the TemplateTag.
        """
        return f'<{self.__class__.__name__} "{self.tagname}" takes_context={self.takes_context}>'


class BlockTemplateTag(TemplateTag):
    """
    Template tag which acts as a block level template tag.
    
    To use this, name and tagcallable arguments should be provided.
    
    Notes:
        - The tagcallable should be a callable object accepting context as first argument if takes_context=True,
        and the second argument as the content wrapped between the tags.
        - The tagcallable should always return the new modified content after processing.
        
    Example:
        
        def do_something(content):
            # process and modify content logic
            return content
            
        tag = BlockTemplateTag("some_name", tagcallable=do_something)
    """
    def register_in_django(self, library):
        """
        Register this tag in a Django template library.

        Args:
            library: The Django template library to register the tag with.
        """
        from django import template
        
        root_tag = self
        
        class CustomBlockNode(template.Node):
            """
            CustomBlockNode class for all block level tags.
            """
            def __init__(self, nodelist, *args, **kwargs):
                self.nodelist = nodelist
                self.args = args
                self.kwargs = kwargs
        
            def render(self, context):
                # Render the block content
                content = self.nodelist.render(context)
                if root_tag.takes_context:
                    return root_tag.tagcallable(context, content)
                return root_tag.tagcallable(content)
        
        @library.tag(name=self.tagname)
        def django_tag_wrapper(parser, token):
            try:
                # Parse the tag's arguments and keyword arguments
                tokens = token.split_contents()
                tag_name = tokens.pop(0)  # Remove the tag name
        
                args = []
                kwargs = {}
                for token in tokens:
                    if "=" in token:
                        key, value = token.split("=", 1)
                        kwargs[key] = parser.compile_filter(value)  # Compile for runtime resolution
                    else:
                        args.append(parser.compile_filter(token))  # Compile for runtime resolution
        
                # Parse the block content
                nodelist = parser.parse((f"end{tag_name}",))
                parser.delete_first_token()
        
                # Return the custom block node
                return CustomBlockNode(nodelist, *args, **kwargs)
            except Exception as e:
                raise template.TemplateSyntaxError(f"Error parsing custom block tag: {e}")
    
    def register_in_jinja2(self, environment):
        """
        Register this tag as a block-level tag in a Jinja2 environment.
    
        Args:
            environment: The Jinja2 environment to register the tag with.
        """
        root_tag = self
        
        class CustomBlockExtension(Extension):
            # Define the tag name
            tags = {root_tag.tagname}
        
            def __init__(self, environment):
                super(CustomBlockExtension, self).__init__(environment)
                
            def parse(self, parser):
                lineno = next(parser.stream).lineno
                body = parser.parse_statements([f'name:end{root_tag.tagname}'], drop_needle=True)
                return nodes.CallBlock(self.call_method('_render_customblock', [nodes.ContextReference()]), [], [], body).set_lineno(lineno)
        
            def _render_customblock(self, context, caller):
                # Access context data here
                content = caller()
                # Process the content as needed
                if root_tag.takes_context:
                    return root_tag.tagcallable(context, content)
                return root_tag.tagcallable(content)
        
        # Dynamically register the extension
        CustomBlockTagClass = type(f"CustomBlockTagExtension_{root_tag.tagname}", (CustomBlockExtension,), {})
        environment.add_extension(CustomBlockTagClass)


class TemplateFilter:
    """
    Base Class for template Filter.

    This will be used to register this filter to a template.

    Notes:
        - TemplateFilter does not support takes_context. You need to parse the context directly if you need it.

        Example:
                {{ variable | myfilter:context }}

    Form:
        {{ variable | myfilter }}
    """

    __all_filters = defaultdict(str)

    # Dictionary for all created filters

    def __init__(self, filtername: str, filtercallable: Callable):
        self.filtername = filtername
        self.filtercallable = filtercallable

        # Improved assertions with clearer error messages and more explicit checks
        
        assert isinstance(filtername, str), \
            f"Argument 'filtername' should be a string, but got {type(filtername).__name__} instead."
        
        assert filtername, "Argument 'filtername' cannot be an empty string."
        
        assert callable(filtercallable), \
            f"Argument 'filtercallable' should be callable, but got {type(filtercallable).__name__} instead."
        
        if not self.__all_filters[filtername]:
            type(self).__all_filters[filtername] = self
        else:
            raise TemplateFilterError(
                f"Repeated template filter '{filtername}', already exists")

    @classmethod
    def get_filter(cls, filtername: str):
        """
        Retreive a created Template Filter with provided name.

        Raises:
            TemplateFilterError: If filter with provided name does'nt exist.
        """
        filter = cls.__all_filters.get(filtername)
        if not filter:
            raise TemplateFilterError(
                f"Template Filter with name '{filtername}' was never created.")
        return filter
    
    def register_in_django(self, library):
        """
        Register this filter in a Django template library.

        Args:
            library: The Django template library to register the filter with.
        """
        
        @library.filter(name=self.filtername)
        def django_filter_wrapper(_obj, *args, **kwargs) -> MarkupSafeString:
            return self.filtercallable(_obj, *args, **kwargs)

    def register_in_jinja2(self, environment):
        """
        Register this filter in a Jinja2 environment.

        Args:
            environment: The Jinja2 environment to register the filter with.
        """
        environment.filters[self.filtername] = self.filtercallable

    def __repr__(self):
        """
        Returns a string representation of the TemplateFilter.

        Returns:
            str: String representation of the TemplateFilter.
        """
        return f'<{self.__class__.__name__} "{self.filtername}">'
