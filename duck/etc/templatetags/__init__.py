"""
Module for default builtin duck template tags and filters.
"""
from urllib.parse import urljoin

from duck.template.templatetags import (
    TemplateTag,
    TemplateFilter,
    BlockTemplateTag,
)
from duck.utils.path import (
    is_good_url_path,
    sanitize_path_segment, 
)
from duck.utils.safemarkup import (
    MarkupSafeString,
    mark_safe, 
)
from duck.meta import Meta
from duck.settings import SETTINGS
from duck.template.csrf import get_csrf_token
from duck.shortcuts import resolve
from duck.etc.templatetags.react_frontend import react_frontend


def wrapped_resolve(*args, **kw):
    """
    Resolves URL associated with a name
    """
    # wrapped function to call resolve to avoid circular import.
    url = resolve(*args, **kw)
    return url


@mark_safe
def csrf_token(context) -> MarkupSafeString:
    """
    Retrieves CSRF html input field.
    """
    request = context.get("request")
    name = "csrfmiddlewaretoken"
    if not SETTINGS["USE_DJANGO"]:
        token = get_csrf_token(request)  # csrf_token
    else:
        from django.middleware.csrf import get_token
        token = get_token(request)
    return f'<input id="{name}" name="{name}" type="hidden" value="{token}">'


def static(resource_path: str):
    """
    Returns static url for the provided resource.
    """
    if not is_good_url_path(resource_path):
        raise TypeError(
            f"Please provide valid url path in form '/some/path' not {resource_path}"
        )
    try:
        root_url = Meta.get_absolute_server_url() # get absolute server url
    except Exception:
        root_url = "/"
    static_url = SETTINGS["STATIC_URL"]
    static_url = sanitize_path_segment(static_url)
    resource_path = sanitize_path_segment(resource_path).lstrip("/")
    static_url = urljoin(root_url, static_url) + "/"
    return urljoin(static_url, resource_path)


def media(resource_path: str):
    """
    Returns media url for the provided resource.
    """

    if not is_good_url_path(resource_path):
        raise TypeError(
            f"Please provide valid url path in form '/some/path' not {resource_path}"
        )
    try:
        root_url = Meta.get_absolute_server_url() # get absolute server url
    except Exception:
        root_url = "/"
    media_url = SETTINGS["MEDIA_URL"]
    media_url = sanitize_path_segment(media_url)
    resource_path = sanitize_path_segment(resource_path).lstrip("/")
    media_url = urljoin(root_url, media_url) + "/"
    return urljoin(media_url, resource_path)


csrf_tag = TemplateTag(
    tagname="csrf_token",
    tagcallable=csrf_token,
    takes_context=True,
)

static_tag = TemplateTag(
    tagname="static",
    tagcallable=static,
)

media_tag = TemplateTag(
    tagname="media",
    tagcallable=media
)

resolve_tag = TemplateTag(
    tagname="resolve",
    tagcallable=wrapped_resolve,
)

react_fronted_tag = BlockTemplateTag(
    tagname="react_frontend",
    tagcallable=react_frontend,
    takes_context=True,
)

BUILTIN_TEMPLATETAGS = [
    csrf_tag,
    static_tag,
    media_tag,
    resolve_tag,
    react_fronted_tag,
    # builtin template filters following
]
