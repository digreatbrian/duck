"""
Module containing Duck's default site contact view.
"""

from duck.http.request import HttpRequest
from duck.shortcuts import render

from . import context


def ducksite_contact_view(request: HttpRequest):
    """
    Contact view for Duck's default site.
    """
    ctx = context.get_default_context()

    if request.method.upper() == "POST":
        ctx["feedback_submitted"] = True

    return render(request, "contact.html", ctx, engine="django")
