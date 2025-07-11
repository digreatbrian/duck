"""
This module provides various utility functions and shortcuts for handling 
common operations in the Duck framework. 

It includes functions for rendering templates, generating responses, 
resolving URLs, managing CSRF tokens, handling static and media resources, 
and manipulating HTTP responses.

The module also defines `URLResolveError`, an exception raised when 
URL resolution fails.
"""
import io

from typing import Optional, Any, Union
from functools import lru_cache

from duck import template as _template
from duck.settings import SETTINGS
from duck.http.request import HttpRequest
from duck.http.response import (
    BaseResponse,
    HttpNotFoundResponse,
    HttpRedirectResponse,
    HttpResponse,
    TemplateResponse,
    JsonResponse,
    StreamingHttpResponse,
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
from duck.contrib.responses.errors import get_404_error_response
from duck.contrib.sync import sync_to_async
from duck.exceptions.all import (
    RouteNotFoundError,
    TemplateError,
)

from duck.meta import Meta
from duck.routes import RouteRegistry


__all__ = [
    "simple_response",
    "template_response",
    "URLResolveError",
    "jinja2_render",
    "django_render",
    "render",
    "async_render",
    "redirect",
    "jsonify",
    "not_found404",
    "merge",
    "content_replace",
    "replace_response",
    "resolve",
    "to_response",
    "static",
    "media",
    "csrf_token",
]


class URLResolveError(Exception):
    """
    Raised if URL resolving fails.
    """


def csrf_token(request) -> str:
    """
    Returns the csrf token, whether for django or duck request.
    """
    from duck.template.csrf import get_csrf_token
    
    if not SETTINGS["USE_DJANGO"]:
        token = get_csrf_token(request)  # csrf_token
    else:
        from django.middleware.csrf import get_token
        token = get_token(request)
    return token


@lru_cache(maxsize=128)
def static(resource_path: str) -> str:
    """
    Returns the absolute static url path for provided resource.
    """
    from duck.etc.templatetags import static
    return static(resource_path)


@lru_cache(maxsize=128)
def media(resource_path: str) -> str:
    """
    Returns the absolute media url path for provided resource.
    """
    from duck.etc.templatetags import media
    return media(resource_path)


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
    template = sanitize_path_segment(template).lstrip("/") if template else template

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
    template = sanitize_path_segment(template).lstrip("/") if template else template

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
    engine: str = "django",
    **kw,
) -> TemplateResponse:
    """
    Renders a template and returns the response.

    Args:
            request (HttpRequest): Http request object.
            template (str): Template path within the TEMPLATE_DIR.
            context (dict, optional): Dictionary respresenting template context.
            engine (str, optional): Template engine to use for rendering template, defaults to 'django'.
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


async def async_render(
    request,
    template: str,
    context: dict = {},
    engine: str = "django",
    **kw,
) -> TemplateResponse:
    """
    Asynchronously renders a template and returns the response.

    Args:
            request (HttpRequest): Http request object.
            template (str): Template path within the TEMPLATE_DIR.
            context (dict, optional): Dictionary respresenting template context.
            engine (str, optional): Template engine to use for rendering template, defaults to 'django'.
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
            return await sync_to_async(jinja2_render)(request, template, context, **kw)
        else:
            return await sync_to_async(django_render)(request, template, context, **kw)
    except Exception as e:
        _e = e
        e = str(e)
        if "Syntax error" in e or "syntax error" in e:
            raise TemplateError(
                f"Error rendering template, make sure you are using right template engine: {e}"
            ) from _e
        else:
            raise _e  # reraise error


def redirect(location: str, permanent: bool = False, content_type="text/html", **kw):
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


def jsonify(data: Any, status_code: int = 200, **kw):
    """
    Returns a JsonResponse object

    Args:
        data (Any): Json serializable data
        status_code (int): The response status code. Defaults to 200.
        **kwargs: Extra keywords to parse to JsonResponse
    
    Returns:
        JsonResponse: The http json response object.
    """
    return JsonResponse(data, status_code=status_code, **kw,) 


def not_found404(request: Optional[HttpRequest] = None, body: str = None) -> HttpResponse:
    """
    Returns a 404 error response, either a simple response or a template response given DEBUG mode is on or off.

    Args:
        request (Optional[HttpRequest]): The target http request.
        body (str, optional): Body for the 404 response.
        
    Returns:
        HttpResponse: The http not found response object.
    """
    if body:
        if SETTINGS['DEBUG']:
            response = template_response(
                HttpNotFoundResponse,
                body=body,
            )
        else:
            response = simple_response(
                HttpNotFoundResponse,
                body=body,
            )
        return response
    return get_404_error_response(request)


def merge(
    base_response: HttpResponse,
    take_response: HttpResponse,
    merge_headers: bool = False,
) -> HttpResponse:
    """
    This merges two http response objects into one http response object

    Notes:
    - By default, this only merge content and content headers.
    - This is useful especially when you have a certain type of HttpResponse (for instance HttpNotFoundResponse) 
       but you want that Base response object to have content of a rendered html file.
    """
    assert isinstance(
        base_response, HttpResponse
    ), f"Argument base_response should be an HttpResponse not {type(base_response)}"
    
    assert isinstance(
        take_response, HttpResponse
    ), f"Argument take_response should be an HttpResponse not {type(take_response)}"

    base_response.content_obj = take_response.content_obj
    
    # Add all content headers from take_response to base response
    base_response.set_content_headers(force_set=True)
    
    if merge_headers:
        base_response.header_obj.headers.update(take_response.header_obj.headers)

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
    assert not isinstance(response, StreamingHttpResponse), "Streaming http response not supported."
    assert isinstance(new_data, str) or isinstance(
        new_data, bytes
    ), "Only string or bytes allowed for new_data"

    new_data = new_data.encode("utf-8") if isinstance(new_data, str) else new_data
    
    if not new_content_type:
        raise ValueError(
            "Please provide new_content_type or any of these `use_existing` for no change, `auto` to "
            "automatically determine content type or any valid content type."
        )
    
    elif new_content_type == "auto":
        new_content_type = None

    elif new_content_type == "use_existing":
        new_content_type = response.content_obj.content_type

    if new_content_filepath == "use_existing":
        new_content_filepath = response.content_obj.filepath

    response.content_obj.set_content(new_data, new_content_filepath, new_content_type)

    # Update content type header
    response.set_content_type_header()

    return response


def replace_response(old_response, new_response) -> HttpResponse:
    """
    Replaces/transforms the old response into a new response object but with some old
    fields except for headers, status and content.
    
    Args:
        old_response (HttpResponse): The response you want to apply modifications to.
        new_response (HttpResponse): The base response you want to get values or reference data from.
        
    Returns:
        HttpResponse: The old response but transformed or combined with new response
    """
    old_response.payload_obj = new_response.payload_obj
    
    if isinstance(old_response, StreamingHttpResponse):
        if isinstance(new_response, StreamingHttpResponse):
            # New and old response are both streaming http responses
            old_response.content_provider = new_response.content_provider
        else:
            # New response is not a streaming http response
            old_response.content_provider = lambda: io.BytesIO(new_response.content)
    else:
        if isinstance(new_response, StreamingHttpResponse):
            raise ValueError("Old response is not compatible with new response, i.e. StreamingHttpResponse")
        old_response.content_obj = new_response.content_obj
    return old_response


def resolve(name: str, absolute: bool = True, fallback_url: Optional[str] = None) -> str:
    """
    This resolves a URL based on name.

    Args:
        name (str): The name of the URL to resolve.
        absolute (bool): This will return the absolute url instead of registered path only but it requires the app to be in running state
        fallback_url (Optional[str]): The fallback url to use if the URL is not found.
        
    ``` {important}
    This function is primarily designed for resolving URLs registered as plain, static paths. 
     
     It is strongly recommended to use this function only with URLs registered in the form:
     `
     pattern = '/url/path'
     `

     Using this function with dynamic URLs (e.g., those containing path parameters or regular expression patterns) will return the raw, unregistered pattern, which is typically not useful for direct use. 
     
     For example, using it with:
     `
     pattern = '/url/<some_input>/path'  
     pattern = '/url/hello*'
     `
         
    will return those patterns as is, and not a resolved URL.
    ```
    
    Raises:
        (URLResolveError): Raised if there is no url associated with the name, url associated with the name is not a plain url
    """
    try:
        info = RouteRegistry.fetch_route_info_by_name(name)
        url = info["url"]
        
        if absolute:
            # build absolute url
            root_url = Meta.get_absolute_server_url()

            # return absolute url
            return build_absolute_uri(root_url, url)
        return "/" + url if not url.startswith("/") else url

    except RouteNotFoundError:
        if fallback_url:
            return fallback_url
        raise URLResolveError(f"No URL in registry is associated with name '{name}' ")


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
            raise TypeError(f"Value '{value}' cannot be converted to http response. Consider these types: {allowed_types}")
        value = HttpResponse("%s" % value)
    return value
