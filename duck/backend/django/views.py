"""
Module containing the default view to handle all Django requests through
 redirecting them to the appropriate Duck view to produce a response.
"""
from typing import Callable
from functools import wraps

from django.http.request import HttpRequest as DjangoHttpRequest
from django.http.response import HttpResponse as DjangoHttpResponse

from duck.http.response import BaseResponse
from duck.backend.django.utils import (
    django_to_duck_request,
    duck_to_django_response,
)
from duck.exceptions.all import RouteNotFoundError
from duck.logging import logger
from duck.routes import RouteRegistry
from duck.meta import Meta
from duck.shortcuts import (
    not_found404,
    to_response,
)


def request_meta_update(func: Callable):
    """
    Decorator to ensure that the Django request.META gets updated 
    with the Duck request.META before processing the function.
    
    Why Do This:
        - Keeps the Django request.META in sync with the Duck request.META.
        - Ensures consistency in metadata between the two request objects.
    
    Args:
        func (Callable): The function to be wrapped.
    
    Returns:
        Callable: The wrapped function with synchronized request.META.
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            # Call the wrapped function
            response = func(request, *args, **kwargs)
            return response
        finally:
             if hasattr(request, 'duck_request'):
                # Ensure the `duck_request` attribute exists on the request
                # Synchronize Duck's request.META with Django's request.META
                request.META.update(request.duck_request.META)
    return wrapper


@request_meta_update
def duck_django_view(
    request: DjangoHttpRequest,
) -> DjangoHttpResponse:
    """
    Django default view to handle requests meant for urlpatterns registered within Duck.

    Args:
        request (DjangoHttpRequest): The Django HTTP request.
        
    Returns:
        DjangoHttpResponse: The corresponding Django HTTP response.
    """
    return _duck_django_view(request)


def _duck_django_view(
    request: DjangoHttpRequest,
) -> DjangoHttpResponse:
    """
    Django default view to handle requests meant for urlpatterns registered within Duck.

    Args:
        request (DjangoHttpRequest): The Django HTTP request.
        
    Returns:
        DjangoHttpResponse: The corresponding Django HTTP response.
    """
    # Convert Django request to Duck request
    duck_request = django_to_duck_request(request)
    request.duck_request = duck_request
    
    # Retrieve route details from Duck app's route registry
    try:
        route_info = RouteRegistry.fetch_route_info_by_url(duck_request.path)
        url = route_info["url"]
        handler_kwargs = route_info["handler_kwargs"]
        # Call the Duck view with the necessary parameters
        duck_view = route_info["handler"]
        duck_response = duck_view(duck_request, **handler_kwargs)
    except RouteNotFoundError:
        duck_response = not_found404()
    
    except Exception as e:
        logger.log_raw(
            f'Error invoking response view for URL "{duck_request.path}": {str(e)}',
            level=logger.ERROR,
            custom_color=logger.Fore.YELLOW,
        )
        raise e
    
    try:
        duck_response = to_response(duck_response)
    except TypeError as e:
        raise TypeError(f"View for URL '{url}' returned object of unallowed type.") from e
    
    # Convert Duck Response to DjangoHttpResponse
    django_response = duck_to_django_response(duck_response)
    
    return django_response
