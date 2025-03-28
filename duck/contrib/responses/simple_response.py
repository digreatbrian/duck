"""
This module provides a shortcut to create a simple response with a given response class and icon link.
"""

import os
from typing import Type

from duck.http.response import HttpResponse
from duck.storage import duck_storage
from duck.utils.safemarkup import mark_safe


with open(
    os.path.join(duck_storage,
                       "etc/templates/simple_response.html")) as fd:
    simple_response_html = fd.read()


with open(os.path.join(duck_storage,
                       "etc/templates/simple_icon_response.html")) as fd:
    simple_icon_response_html = fd.read()


class SimpleResponseError(Exception):
    """
    Simple response related errors.
    """


def _make_simple_response(
    response_class: Type[HttpResponse],
    title: str = None,
    heading: str = None,
    body: str = None,
    icon_link: str = None,
    icon_type="image/png",
) -> HttpResponse:
    """
    Transforms a basic response like HttpServerErrorResponse into a nicer simple response.

    Args:
        response_class (Type[HttpResponse]): The response class to be transformed.
        title (str): The title of the response, If not provided, response.status_message is used (optional).
        heading (str): The heading of the response. If not provided, response.status_message is used (optional).
        body (str): The body of the response. If not provided, response.status_explanation is used (optional).
        icon_link (str): The link to the icon (optional).
        icon_type (str): The type of the icon (optional).

    Raises:
        SimpleResponseError: If the response class is not a subclass of HttpResponse.
        SimpleResponseError: If the icon type is not provided when an icon link is provided.

    Returns:
        HttpResponse: The transformed response.
    """
    from duck.shortcuts import content_replace

    if not issubclass(response_class, HttpResponse):
        raise SimpleResponseError(
            "The response class must be a subclass of HttpResponse.")

    response = response_class()
    body = body or ""
    body = mark_safe(body)

    if not icon_link:
        data = simple_response_html.format(
            title=title or response.status_message,
            heading=heading or response.status_message,
            explanation=body or response.status_explanation,
        )
    else:
        if not icon_type:
            raise SimpleResponseError(
                "The icon type must be provided when an icon link is provided."
            )
        data = simple_icon_response_html.format(
            title=title or response.status_message,
            heading=heading or response.status_message,
            explanation=body or response.status_explanation,
            icon_link=icon_link,
            icon_type=icon_type,
        )
    response = content_replace(response, data)
    return response


def simple_response(
    response_class: Type[HttpResponse],
    title: str = None,
    heading: str = None,
    body: str = None,
    icon_link="/static/images/duck-favicon.png",
    icon_type="image/png",
) -> HttpResponse:
    """
    Transforms a basic response like HttpServerErrorResponse into a nicer simple response.
    
    Args:
        response_class (Type[HttpResponse]): The response class to be transformed.
        title (str): The title of the response, If not provided, response.status_message is used (optional).
        heading (str): The heading of the response. If not provided, response.status_message is used (optional).
        body (str): The body of the response. If not provided, response.status_explanation is used (optional).
        icon_link (str): The link to the icon (optional).
        icon_type (str): The type of the icon (optional).

    Raises:
        SimpleResponseError: If the response class is not a subclass of HttpResponse.
        SimpleResponseError: If the icon type is not provided when an icon link is provided.

    Returns:
        HttpResponse: The transformed response.
    """
    return _make_simple_response(
        response_class=response_class,
        title=title,
        heading=heading,
        body=body,
        icon_link=icon_link,
        icon_type=icon_type,
    )
