"""
Module containing template specific classes.
"""

import os
import pathlib
import jinja2

from functools import partial
from typing import Dict, List, Optional, Union

from duck.exceptions.all import (
    DjangoTemplateError,
    TemplateError,
)
from duck.template.templatetags import (
    TemplateFilter,
    TemplateTag,
)
from duck.utils.path import joinpaths
from duck.settings import SETTINGS


class Template:
    """
    Template class for all base templates.
    """

    def __init__(
        self,
        template_data: Optional[str] = None,
        context: Optional[Dict] = None,
        name: Optional[str] = None,
        origin: Optional[str] = None,
        engine=None,
    ):
        """
        Initialize template class.

        Args:
            template_data (str, optional): The template code/data.
            context (dict, optional): The template context
            name (str, optional): The name of the template. Name will be resolved from origin.
            origin (str, optional): The asolute template path.
            engine: The template engine.
        """
        self.template_data = template_data
        self.context = context or {}
        self.origin = origin
        self.name = name or pathlib.Path(origin).basename() if origin else name
        self.engine = engine or Engine.get_default()

    def render_template(self) -> str:
        return self.engine.render_template(self)


class Engine:
    """
    Engine class for templates.

    Notes:
        For all engines, Duck internal and custom template tags and filters are enabled by default.
    """

    @classmethod
    def get_default(cls):
        """
        Returns the default template engine, ie. Jinja2Engine.
        """
        return Jinja2Engine()

    def get_blueprint_template_dirs(self):
        """
        Returns a generator for the template directories for all blueprints.
        """
        from duck.settings.loaded import BLUEPRINTS

        for blueprint in BLUEPRINTS:
            if blueprint.enable_template_dir:
                template_dir = joinpaths(blueprint.root_directory,
                                         blueprint.template_dir)
                yield template_dir

    @property
    def template_dirs(self) -> List:
        """
        Returns the template directories for entire app scope.
        """
        template_dirs = []
        custom_template_dirs = str(SETTINGS["TEMPLATE_DIRS"])
        blueprint_template_dirs = self.get_blueprint_template_dirs()

        template_dirs.extend(custom_template_dirs)
        for i in blueprint_template_dirs:
            template_dirs.append(i) if i not in template_dirs else None
        return template_dirs

    def render_template(self, template: Template):
        """
        Returns rendered content.
        """
        raise NotImplementedError("Implement method `render_template`.")


class Jinja2Engine(Engine):
    """
    Jinja2 engine class.
    """

    def __init__(
        self,
        autoescape: bool = True,
        custom_templatetags: Optional[List[TemplateTag | TemplateFilter]] = None,
        environment: Optional[jinja2.Environment] = None,
    ):
        from duck.settings.loaded import ALL_TEMPLATETAGS
        
        self._duck_templatetags = ALL_TEMPLATETAGS
        self.autoescape = autoescape
        self.custom_templatetags = custom_templatetags or []
        self.environment = environment or self.get_default_environment()
        self.setup_environment()

    def get_default_environment(self) -> jinja2.Environment:
        """
        Returns the appropriate jinja2 environment.
        """
        if not hasattr(self, "_jinja2__environment"):
            self._jinja2__environment = jinja2.Environment(
                loader=jinja2.FileSystemLoader(self.template_dirs))
        return self._jinja2__environment

    def apply_templatetags(
        self,
        templatetags: Optional[List[Union[TemplateTag, TemplateFilter]]] = None,
     ):
        """
        This applies template tags or filters to the jinja2 environment.
        
        Args:
            templatetags (Optional[List[Union[TemplateTag, TemplateFilter]]],): List of template tags or filters.
        """
        templatetags = templatetags or []
        for tag_or_filter in templatetags:
            tag_or_filter.register_in_jinja2(self.environment)
    
    def setup_environment(self):
        """
        Setups the jinja2 environment.
        """
        self.environment.autoescape = self.autoescape
        self.apply_templatetags(
            self._duck_templatetags
            + self.custom_templatetags
        ) # apply a tags and filters available in Duck project.
        
    def render_template(self, template: Template) -> str:
        """
        This renders a template into static content.

        Args:
            template (Template): The template object.

        Returns:
            rendered_template (str): Rendered template as string
        """
        if not isinstance(template, Template):
            raise TemplateError(
                f"The template object should be an instance of Template not {type(template)}"
            )
        try:
            jinja2_template = self.environment.get_template(template.name)
            return jinja2_template.render(template.context)
        except jinja2.exceptions.TemplateNotFound:
            raise TemplateError(
                f"Template `{template.origin or template.name or template}` doesn't exist. "
                f"If using a blueprint, ensure that blueprint.enable_template_dir=True."
            )
        except Exception as e:
            raise TemplateError(
                f"Error occurred while rendering the template `{template.origin or template.name or template}`: {str(e)}"
            ) from e


class DjangoEngine(Engine):
    """
    Django engine class.
    """

    def __init__(
        self,
        autoescape: bool = True,
        libraries: Optional[List[str]] = None,
        _django_engine: Optional = None,
    ):
        self._duck_templatetags: List[str] = ["duck.backend.django.templatetags.ducktags"]  # all internal and custom template tags and filters
        self.autoescape = autoescape
        self.libraries = libraries
        self._django_engine = (_django_engine
                               or self.get_default_django_engine())
        self.setup_django_engine()

    @classmethod
    def get_default(cls):
        """
        Returns the default Django engine.
        """
        return DjangoEngine()

    def get_default_django_engine(self):
        """
        Returns the django default template engine.
        """
        from django import setup
        from django.template import Engine as _Engine

        os.environ.setdefault(
            "DJANGO_SETTINGS_MODULE",
            "backend.django.duckapp.duckapp.settings",
        )  # set django settings if not set
        
        setup()
        
        if not hasattr(self, "_django__engine"):
            self._django__engine = _Engine.get_default()
        return self._django__engine

    def apply_templatetags(
        self,
        builtin_libraries: Optional[List[str]] = None,
        custom_libraries: Optional[Dict[str, str]] = None
     ):
        """
        This applies template tags or filters to the engine.
        """
        if builtin_libraries:
            # register builtin libraries to engine.
            builtins = self._django_engine.get_template_builtins(builtin_libraries)
            self._django_engine.builtins.extend(builtin_libraries)
            self._django_engine.template_builtins.extend(builtins)

        if custom_libraries:
            # add custom libraries
            libraries = self._django_engine.get_template_libraries(custom_libraries)
            self._django_engine.libraries.update(custom_libraries)
            self._django_engine.template_builtins.extend(libraries)
    
    def setup_django_engine(self):
        """
        Setups the inner django engine.
        """
        self._django_engine.autoescape = self.autoescape
        self._django_engine.dirs.extend(self.template_dirs)
        self.apply_templatetags(
            builtin_libraries=self._duck_templatetags,
            custom_libraries=self.libraries,
        )
        
    def render_template(self, template: Template):
        """
        Returns rendered content.
        """
        from django.template import Context

        if not isinstance(template, Template):
            raise TemplateError(
                f"The template object should be an instance of Template not {type(template)}"
            )
        try:
            _template = self._django_engine.get_template(template.name)
            return _template.render(Context(template.context))
        except Exception as e:
            raise DjangoTemplateError(str(e)) from e
