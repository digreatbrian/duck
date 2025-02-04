"""
Duck shortcuts, etc.
"""

from typing import Optional, Any, Union

from duck import template as _template
from duck.settings import SETTINGS
from duck.http.request import HttpRequest
from duck.http.response import (
    BaseResponse,
    HttpNotFoundResponse,
    HttpRedirectResponse,
    HttpResponse,
    TemplateResponse,
)
from duck.utils.path import (
    build_absolute_uri,
    sanitize_path_segment,
    is_good_url_path,
)
from duck.contrib.responses import (
    simple_response,
    template_response,
)
from duck.exceptions.all import RouteNotFoundError, TemplateError
from duck.meta import Meta
from duck.routes import RouteRegistry


__all__ = [
    "simple_response",
    "template_response",
    "URLResolveError",
    "jinja2_render",
    "django_render",
    "render",
    "redirect",
    "not_found404",
    "merge",
    "content_replace",
    "resolve",
    "to_response",
]


class URLResolveError(Exception):
    """
    Raised if URL resolving fails.
    """


def jinja2_render(
    request: HttpRequest,
    template: str,
    context: dict = {},
    **kw,
) -> TemplateResponse:
    """
    Render a jinja2 template.

    Args:
        request (HttpRequest): The request object.
        template (str): The Jinja2 template.
        context (dict, optional): The context dictionary to pass to the template. Defaults to an empty dictionary.
        **kw: Additional keyword arguments to parse to TemplateResponse.

    Returns:
        TemplateResponse: The response object with the rendered content.
    """
    template = (
        sanitize_path_segment(template).lstrip("/")
        if template else template)
    
    return TemplateResponse(
        request=request,
        template=template,
        context=context,
        engine=_template.environment.Jinja2Engine.get_default(),
        **kw,
    )


def django_render(
    request: HttpRequest,
    template: str,
    context: dict = {},
    **kw,
) -> TemplateResponse:
    """
    Render a Django template.

    Args:
        request (HttpRequest): The request object.
        template (str): The Django template.
        context (dict, optional): The context dictionary to pass to the template. Defaults to an empty dictionary.
        **kw: Additional keyword arguments to parse to DjangoTemplateResponse.

    Returns:
        TemplateResponse: The response object with the rendered Django template.
    """
    template = (
        sanitize_path_segment(template).lstrip("/")
        if template else template)
    
    return TemplateResponse(
        request=request,
        template=template,
        context=context,
        engine=_template.environment.DjangoEngine.get_default(),
        **kw,
    )


def render(
    request,
    template: str,
    context: dict = {},
    engine: str = "jinja2",
    **kw,
) -> TemplateResponse:
    """
    Renders a template and returns the response.

    Args:
            request (HttpRequest): Http request object.
            template (str): Template path within the TEMPLATE_DIR.
            context (dict, optional): Dictionary respresenting template context.
            engine (str, optional): Template engine to use for rendering template, defaults to 'jinja2'.
            **kw: Additional keywords to parse to the http response for the current template engine.

    Returns:
            TemplateResponse: Http response rendered using Django or Jinja2.
    """
    allowed_engines = {"jinja2", "django"}
    
    if engine not in allowed_engines:
        raise TemplateError(
            f"Provided engine not recognized, should be one of ['jinja2', 'django'] not '{engine}' "
        )
    try:
        if engine == "jinja2":
            return jinja2_render(request, template, context, **kw)
        else:
            return django_render(request, template, context, **kw)
    except Exception as e:
        _e = e
        e = str(e)
        if "Syntax error" in e or "syntax error" in e:
            raise TemplateError(
                f"Error rendering template, make sure you are using right template engine: {e}"
            ) from _e
        else:
            raise _e  # reraise error


def redirect(
    location: str,
    permanent: bool = False,
    content_type="text/html",
    **kw):
    """
    Returns a HttpRedirectResponse object

    Args:
        location (str): URL location
        permanent (bool): Whether this is a permanent redirect, defaults to False
        content_type (str): Content type for response, defaults to 'text/html'
        **kw: Keyword arguments to parse to HttpRedirectResponse

    Returns:
        HttpRedirectResponse: The http redirect response object.
    """
    return HttpRedirectResponse(
        location=location,
        content_type=content_type,
        permanent=permanent,
        **kw,
    )


def not_found404(
    body: Optional[str] = None,
    content_type="text/html",
    **kw):
    """Returns a 404 HttpNotFoundResponse object either a simple response or a template response given DEBUG mode is on or off.

    Args:
        content (Optional[body]): Body for the response, defaults to None
        content_type (str): Content type for response, defaults to 'text/html'
        **kw: Keyword arguments to parse to HttpNotFoundResponse

    Returns:
        HttpNotFoundResponse: The http not found response object.
    """
    if SETTINGS["DEBUG"]:
        return template_response(HttpNotFoundResponse, body=body)
    return simple_response(HttpNotFoundResponse)


def merge(
    base_response: HttpResponse,
    take_response: HttpResponse,
    merge_headers: bool = False,
) -> HttpResponse:
    """
    This merges two http response objects into one http response object

    Notes:
            By default, this only merge content and content headers.
            This is useful esp when you have a certain type of HttpResponse (for instance HttpNotFoundResponse) but you want that Base response object to have content of a rendered html file.

    """
    assert isinstance(
        base_response, HttpResponse
    ), f"Argument base_response should be an HttpResponse not {type(base_response)}"
    assert isinstance(
        take_response, HttpResponse
    ), f"Argument take_response should be an HttpResponse not {type(take_response)}"

    base_response.content_obj = take_response.content_obj

    base_response.set_content_headers(
        force_set=True
    )  # add all content headers from take_response to base response

    if merge_headers:
        base_response.header_obj.headers.update(
            take_response.header_obj.headers)

    return base_response


def content_replace(
    response: HttpResponse,
    new_data: Union[bytes, str],
    new_content_type: str = "auto",
    new_content_filepath: str = "use_existing",
):
    """
    Replaces response content with new content.

    Args:
                response (HttpResponse): Response to replace content for.
                new_data (Union[bytes, str]): String or bytes to set for content.
                new_content_type (str): The new content type, Defaults to `auto` to automatically determine the content type.
                new_content_filepath (str): Filepath to the content, Defaults to "use_existing" to use the already set filepath.

    """
    assert isinstance(new_data, str) or isinstance(
        new_data, bytes), "Only string or bytes allowed for new_data"

    new_data = (new_data.encode("utf-8")
                if isinstance(new_data, str) else new_data)
    if not new_content_type:
        raise ValueError(
            "Please provide new_content_type or any of these `use_existing` for no change, `auto` to "
            "automatically determine content type or any valid content type.")
    elif new_content_type == "auto":
        new_content_type = None

    elif new_content_type == "use_existing":
        new_content_type = response.content_obj.content_type

    if new_content_filepath == "use_existing":
        new_content_filepath = response.content_obj.filepath

    response.content_obj.set_content(new_data, new_content_filepath,
                                     new_content_type)

    # update content type header
    response.set_content_type_header()

    return response


def resolve(name: str, absolute: bool = True) -> str:
    """
    This resolves a URL based on name.

    Args:
        absolute (bool): This will return the absolute url instead of registered path only but it requires the app to be in running state

    Notes:
        It only works on URL's that were registered as plain urls in form:
            pattern = '/url/path'

            # not
            pattern = '/url/<some_input>/path'
            # or
            pattern = '/url/hello*'

    Raises:
        (URLResolveError): Raised if there is no url associated with the name, url associated with the name is not a plain url
    """
    try:
        info = RouteRegistry.fetch_route_info_by_name(name)
        url = info["url"]

        if not is_good_url_path(url):
            raise URLResolveError(
                f"Only plain URL's associated with the name '{name}' is malformed or invalid")

        if absolute:
            # build absolute url
            root_url = Meta.get_absolute_server_url()

            # return absolute url
            return build_absolute_uri(root_url, url)
        return "/" + url if not url.startswith("/") else url

    except RouteNotFoundError:
        raise URLResolveError(
            f"No URL in registry is associated with name '{name}' ")


def to_response(value: Any) -> Union[BaseResponse, HttpResponse]:
    """
    Converts any value to http response.
    
    Notes:
        - If value is already a response object, nothing will be done.
        
    Raises:
        TypeError: If the value is not convertable to http response.
    """
    allowed_types = (int, str, float, dict, list, set)
    
    if not isinstance(value, BaseResponse):
        if not isinstance(value, allowed_types):
              raise TypeError(
                  f"Value '{value}' cannot be converted to http response. Consider these types: {allowed_types}"
               )
        value = HttpResponse("%s" % value)
    return value
