"""
Module containing Duck's internal template engine.
"""

from duck.storage import duck_storage
from duck.template.environment import Jinja2Engine
from duck.utils.path import joinpaths


class InternalDuckEngine(Jinja2Engine):
    """
    InternalDuckEngine class representing duck's internal template engine,
    meaning this engine is focused only on retreiving templates that are within the duck internal
    storage.
    """

    @property
    def template_dirs(self):
        return joinpaths(duck_storage, "etc/templates")

    @classmethod
    def get_default(self):
        """
        Returns the default internal duck engine.
        """
        # in short, this returns InternalDuckEngine instance with default settings
        return InternalDuckEngine()
