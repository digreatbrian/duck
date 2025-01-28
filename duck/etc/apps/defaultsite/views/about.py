"""
Module containing Duck's default site about view.
"""

from duck.http.request import HttpRequest
from duck.shortcuts import render

from . import context


def ducksite_about_view(request: HttpRequest):
    """
    About view for Duck's default site.
    """
    ctx = context.get_default_context()
    return render(request, "about.html", ctx)
