"""
Module containing Duck's default site home view.
"""

from duck.http.request import HttpRequest
from duck.shortcuts import render

from . import context


def ducksite_home_view(request: HttpRequest):
    """
    Home view for Duck's default site.
    """
    ctx = context.get_default_context()
    return render(request, "home.html", ctx)
