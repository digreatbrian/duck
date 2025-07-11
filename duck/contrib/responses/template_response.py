"""
This module provides a shortcut to create a better-mid response with a given response class and icon link.
"""
import os

from typing import Type

from duck.etc.internals.template_engine import InternalDuckEngine
from duck.http.response import HttpResponse, TemplateResponse
from duck.settings import SETTINGS
from duck.utils.path import joinpaths
from duck.utils.safemarkup import mark_safe


FAVICON = os.getenv("SIMPLE_RESPONSE_DEFAULT_ICON") or joinpaths(str(SETTINGS["STATIC_URL"]), "duck-favicon.png")


def template_response(
    response_class: Type[HttpResponse],
    title: str = None,
    heading: str = None,
    body: str = None,
    icon_link=FAVICON,
    icon_type="image/png",
    debug: bool = SETTINGS["DEBUG"],
) -> TemplateResponse:
    """
    Transforms a basic response like HttpServerErrorResponse into a nicer Duck response.

    Args:
        response_class (Type[HttpResponse]): The response class to be transformed.
        title (str): The title of the response, If not provided, response.status_message is used (optional).
        heading (str): The heading of the response. If not provided, response.status_message is used (optional).
        body (str): The body of the response. If not provided, response.status_explanation is used (optional).
        icon_link (str): The link to the icon (optional).
        icon_type (str): The type of the icon (optional).
        debug (bool): Whether to render template in debug mode. Defaults to the one set in settings.py

    Returns:
        TemplateResponse: The transformed response.
    """
    response = response_class()
    context = {}
    context["title"] = title or response.status_message
    context["heading"] = heading or response.status_message
    context["body"] = mark_safe(body or response.status_explanation)
    context["icon_link"] = icon_link
    context["icon_type"] = icon_type
    context["debug"] = debug

    if not issubclass(response_class, HttpResponse):
        raise TypeError("The response class must be a subclass of HttpResponse.")
    
    if icon_link and not icon_type:
        raise TypeError("The icon type must be provided when an icon link is provided.")

    response = TemplateResponse(
        request=None,
        template="base_template_response.html",
        context=context,
        content_type="text/html",
        status_code=response.status_code,
        engine=InternalDuckEngine.get_default(),
    )
    return response
