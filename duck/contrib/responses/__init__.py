"""
Module containing functions to quickly transform bare http responses into 
to better responses.
"""

from duck.contrib.responses.simple_response import simple_response
from duck.contrib.responses.template_response import template_response

__all__ = ["simple_response", "template_response"]
