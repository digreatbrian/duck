"""
Module containing RequestProcessor class for processing requests.
"""
import re
import time

from typing import (
    Optional,
    Dict,
    Any,
    Tuple,
)
from functools import lru_cache

from duck.db.hooks import (
    view_wrapper,
    async_view_wrapper,
)
from duck.contrib.sync import (
    convert_to_async_if_needed,
    convert_to_sync_if_needed,
)
from duck.settings import SETTINGS
from duck.settings.loaded import (
    WSGI,
    ASGI,
    MIDDLEWARES,
    NORMALIZERS,
    PROXY_HANDLER,
)
from duck.exceptions.all import (
    MiddlewareError,
    RouteNotFoundError,
    RouteError,
    MethodNotAllowedError,
    RequestError,
)
from duck.http.core.proxyhandler import HttpProxyResponse
from duck.http.middlewares import BaseMiddleware
from duck.http.request import HttpRequest
from duck.http.response import HttpResponse
from duck.routes import RouteRegistry
from duck.shortcuts import to_response        
from duck.logging import logger
from duck.meta import Meta


DJANGO_SIDE_PATTERNS = [re.compile(p) for p in SETTINGS["DJANGO_SIDE_URLS"] or []]

DUCK_EXPLICIT_PATTERNS = [re.compile(p) for p in SETTINGS["DUCK_EXPLICIT_URLS"] or []]


@lru_cache(maxsize=256)
def is_django_side_url(url: str) -> bool:
    """
    Returns whether the request URL is in DJANGO_SIDE_URLS in settings.py,
    this means that the request is meant to be handled by Django directly, and Duck doesn't
    know anything about the urlpattern resolving to this request url.
    """
    return any(p.fullmatch(url) for p in DJANGO_SIDE_PATTERNS)


@lru_cache(maxsize=256)
def is_duck_explicit_url(url: str) -> bool:
    """
    Returns whether the request URL is in DUCK_EXPLICIT_URLS meaning,
    The request with the url doesn't need to be parsed to Django server first to produce a
    response, but rather to be handled by Duck directly.
        
    Notes:
    - This is only useful when USE_DJANGO=True as all requests all proxied to Django server to
      generate the http response.
    """
    # Duck explicit URLs are urls not to be proxied to Django even if USE_DJANGO=True.
    # They are handled directly by within Duck.
    return any(p.fullmatch(url) for p in DUCK_EXPLICIT_PATTERNS)

        
class RequestProcessor:
    """
    RequestProcessor class for enforcing middleware checks and processing requests.
    """
    __slots__ = ("request", "_route_info")
    
    def __init__(self, request: HttpRequest):
        """
        Initializes the request processor.

        Args:
                request (HttpRequest): HttpRequest object to process
        """
        assert isinstance(request, HttpRequest), f"Request should be an instance of HttpRequest not `{type(request)}`."
        self.request = request
        self.normalize_request()
    
    @property
    def route_info(self) -> Dict[str, Any]:
        """
        Returns the resolved request route information.
        
        Raturns:
            Dict: The dictionary with the results
        
        Raises:
            RouteNotFoundError: 
                If there is no information on the request path meaning,
                no urlpattern resolving to this request path has been registered.
            RouteError:
                Other route-related errors.
        """
        if not hasattr(self, "_route_info"):
            self._route_info = RouteRegistry.fetch_route_info_by_url(self.request.path)
        return self._route_info
        
    def normalize_request(self):
        """
        Normalizes the request object.
        """
        for normalizer in NORMALIZERS:
            try:
                normalizer.normalize(self.request)
            except Exception as e:
                # Optionally log the normalization error
                if not SETTINGS["IGNORE_NORMALIZATION_ERRORS"]:
                    raise e

    def check_middlewares(self, ) -> tuple[str, Optional[BaseMiddleware]]:
        """
        Checks a request against all configured middlewares in settings.py.

        This method iterates through the middlewares defined in settings and verifies
        if the request meets the requirements imposed by each middleware. If a
        middleware check fails, processing stops and the error middleware is
        returned. Otherwise, the method returns a tuple indicating successful
        request processing ("ok", None).

        Notes:
                - If the request failed to satisfy any middleware, the key "FAIL_MIDDLEWARE" will be set.

        Returns:
            tuple[str, BaseMiddleware]: A tuple containing two elements:
                - str: Indicates the outcome of the middleware checks.
                    - "ok": The request passed all middleware checks.
                    - "bad": The request failed a middleware check.
                - middleware (Optional[BaseMiddleware]): The middleware that the
                    request failed to meet, or None if all checks passed.
        """
        for middleware in MIDDLEWARES:
            if issubclass(middleware, BaseMiddleware):
                middleware_state = convert_to_sync_if_needed(middleware.process_request)(self.request)

                if middleware_state == BaseMiddleware.request_ok:
                    pass
                else:
                    if middleware_state != BaseMiddleware.request_bad:
                        raise MiddlewareError(
                            f"Middleware '{middleware.__name__}' process_request method return unallowed value, should be either BaseMiddleware.request_ok or BaseMiddleware.request_bad."
                        )
                    self.request.META["FAILED_MIDDLEWARE"] = middleware
                    if SETTINGS["MIDDLEWARE_FAILURE_BEHAVIOR"] != "ignore":
                        return "bad", middleware
            else:
                raise MiddlewareError(
                    f"Unknown Middleware: '{middleware.__name__}', expected a sub instance of BaseMiddleware")
        return "ok", None

    def check_base_errors(self):
        """
        Checks base errors within the request.
        
        RequestError: If the request has errors or is malformed anyhow.
        """
        if self.request.error:
            if isinstance(self.request.error, RequestError):
                raise self.request.error
            raise RequestError(f"Request error: {self.request.path}")
        
    def check_errors(self):
        """
        Checks for errors like MethodNotAllowedError and RouteNotFoundError.
        
        Raises:
            MethodNotAllowedError: If the requested method is not allowed for the current request.
            RouteNotFoundError: If the requested url doesn't match any registered routes.
        """
        # Allowed methods validation
        methods = {i.upper() for i in self.route_info["methods"]}
        
        if methods and self.request.method.upper() not in methods:
            raise MethodNotAllowedError("The requested method is not allowed for this request.")
            
    def get_view_response(self) -> HttpResponse:
        """
        Processes the appropriate view for the request and returns appropriate response.

        This is called if request has not failed any of the middleware checks and is considered error free,
        ready to be parsed to the appropriate view to generate response.
        
        Raises:
            MethodNotAllowedError: If the requested method is not allowed for the current request.
            RouteNotFoundError: If the requested url doesn't match any registered routes.
        
        Notes:
        - This also closes Django DB connections if any connection was made in view.
        """
        url = self.request.path
        
        # Check for errors
        self.check_errors()
        
        try:
            url = self.route_info["url"]  # set the url set in registry
            view_kwargs = self.route_info["handler_kwargs"]
            view_callable = self.route_info["handler"]
            
            # Execute the view callable and retrieve the http response
            view_callable = convert_to_sync_if_needed(view_callable)
            response = view_wrapper(view_callable)(request=self.request, **view_kwargs)
            
        except Exception as e:
            logger.log_raw(
                f'\nError invoking response view for URL "{url}" ',
                level=logger.ERROR,
                custom_color=logger.Fore.YELLOW,
            )
            raise e
        
        # Check and convert the data returned by the view to Http response.
        try:
            response = to_response(response)
        except TypeError as e:
            # The data received from the view cannot be converted to http response.
            raise TypeError(f"Invalid data received from response view for URL '{url}'") from e
        return response

    def get_django_response(self) -> HttpProxyResponse:
        """
        Returns the streaming http response fetched from django server.
        
        Raises:
            MethodNotAllowedError: If the requested method is not allowed for the current request.
            RouteNotFoundError: If the requested url doesn't match any registered routes.
        """
        # create proxy handler
        uses_ipv6 = Meta.get_metadata("DUCK_USES_IPV6")
        django_host, django_port = Meta.get_metadata("DUCK_DJANGO_ADDR")
        
        # Check for errors
        try:
            self.check_errors()
        except RouteNotFoundError as e:
            if is_django_side_url(self.request.path):
                # The request is not registered within Duck but in Django, ignore 404 error.
                pass
            else:
                raise e # reraise error
        
        try:
            proxy_handler = PROXY_HANDLER(
                target_host=django_host,
                target_port=django_port,
                uses_ipv6=uses_ipv6,
                uses_ssl=False,
            ) # build a proxy handler
            
            # Ensure http version is HTTP/1.1
            if "/2" in str(self.request.http_version):
                self.request.http_version = "HTTP/1.1"
            
            # Retrieve the http response from django server.
            streaming_proxy_response = proxy_handler.get_response(
                self.request,
                self.request.client_socket,
            )
            
            # Return the http streaming response obtained from django server.
            return streaming_proxy_response
        
        except Exception as e:
            if self.request and hasattr(self.request, "META"):
                self.request.META["DEBUG_MESSAGE"] = f"Bad Gateway: [{django_host}, {django_port}]"
            raise e # Reraise error.

    def get_middleware_error_response(self, middleware) -> HttpResponse:
        """
        Returns middleware error response.
        """
        return convert_to_sync_if_needed(middleware.get_error_response)(self.request)

    def get_response(self, request: HttpRequest) -> HttpResponse:
        """
        Returns the full response for a request, with all middlewares and other configurations applied.
        
        Returns:
            HttpResponse: Http response
        """
        response, disable_logging = WSGI.get_response(request)
        return response
        
    def process_request(self) -> HttpResponse:
        """
        Processes the http request and returns the appropriate http response.
        """
        self.check_base_errors() # check base errors like request syntax error, etc
        
        # Process request further after confirmation that request has no base errors
        # like RequestSyntaxError, RequestUnsupportedVersionError, etc.
        
        # Check for middleware errors.
        state, middleware = self.check_middlewares()
        
        if SETTINGS["MIDDLEWARE_FAILURE_BEHAVIOR"] != "ignore":
            if state == "bad":
                return self.get_middleware_error_response(middleware)
        
        # Return the appropriate view response.
        response = self.get_view_response()
        return response

    def process_django_request(self) -> HttpProxyResponse:
        """
        Processes the request and send it to Django proxy for 
        receiving the appropriate http response.
        """
        self.check_base_errors() # check base errors like request syntax error, etc
        
        # Process request further after confirmation that request has no base errors
        # like RequestSyntaxError, RequestUnsupportedVersionError, etc.
        
        django_side_urls_skip_middlewares = SETTINGS["DJANGO_SIDE_URLS_SKIP_MIDDLEWARES"] # skip middlewares for urls registered in Django.
        django_side_url = is_django_side_url(self.request.path)
        duck_explicit_url = is_duck_explicit_url(self.request.path)
        
        if django_side_url:
            # Request is meant to be handled straight by django,
            # Url pattern for this request is only known by Django.
            if not django_side_urls_skip_middlewares:
                # Check all middlewares
                state, middleware = self.check_middlewares()
                
                if SETTINGS["MIDDLEWARE_FAILURE_BEHAVIOR"] != "ignore":
                    if state == "bad":
                         return self.get_middleware_error_response(middleware)
            
        else:
            # Check all middlewares
            state, middleware = self.check_middlewares()
            if SETTINGS["MIDDLEWARE_FAILURE_BEHAVIOR"] != "ignore":
                if state == "bad":
                         return self.get_middleware_error_response(middleware)
        
        if duck_explicit_url:
            # USE_DJANGO=True but this request is to be handled directly by Duck
            # Request's urlpattern is also known to Django but prefer Duck to handle the request,
            # don't proxy the request to Django server. (only if url is not also django side url)
            if not django_side_url:
                return self.get_view_response()
            
        # Return the appropriate response by proxying request to Django server first
        return self.get_django_response()


class AsyncRequestProcessor(RequestProcessor):
    """
    Asynchronous RequestProcessor class for enforcing middleware checks and processing requests.
    """
    
    async def check_middlewares(self, ) -> tuple[str, Optional[BaseMiddleware]]:
        """
        Checks a request against all configured middlewares in settings.py.

        This method iterates through the middlewares defined in settings and verifies
        if the request meets the requirements imposed by each middleware. If a
        middleware check fails, processing stops and the error middleware is
        returned. Otherwise, the method returns a tuple indicating successful
        request processing ("ok", None).

        Notes:
                - If the request failed to satisfy any middleware, the key "FAIL_MIDDLEWARE" will be set.

        Returns:
            tuple[str, BaseMiddleware]: A tuple containing two elements:
                - str: Indicates the outcome of the middleware checks.
                    - "ok": The request passed all middleware checks.
                    - "bad": The request failed a middleware check.
                - middleware (Optional[BaseMiddleware]): The middleware that the
                    request failed to meet, or None if all checks passed.
        """
        for middleware in MIDDLEWARES:
            if issubclass(middleware, BaseMiddleware):
                middleware_state = await convert_to_async_if_needed(middleware.process_request)(self.request)
                if middleware_state == BaseMiddleware.request_ok:
                    pass
                else:
                    if middleware_state != BaseMiddleware.request_bad:
                        raise MiddlewareError(
                            f"Middleware '{middleware.__name__}' process_request method return unallowed value, should be either BaseMiddleware.request_ok or BaseMiddleware.request_bad."
                        )
                    self.request.META["FAILED_MIDDLEWARE"] = middleware
                    if SETTINGS["MIDDLEWARE_FAILURE_BEHAVIOR"] != "ignore":
                        return "bad", middleware
            else:
                raise MiddlewareError(
                    f"Unknown Middleware: '{middleware.__name__}', expected a sub instance of BaseMiddleware")
        return "ok", None
        
    async def get_view_response(self) -> HttpResponse:
        """
        Processes the appropriate view for the request and returns appropriate response.

        This is called if request has not failed any of the middleware checks and is considered error free,
        ready to be parsed to the appropriate view to generate response.
        
        Raises:
            MethodNotAllowedError: If the requested method is not allowed for the current request.
            RouteNotFoundError: If the requested url doesn't match any registered routes.
        
        Notes:
        - This also closes Django DB connections if any connection was made in view.
        
        """
        url = self.request.path
        
        # Check for errors
        self.check_errors()

        try:
            url = self.route_info["url"]  # set the url set in registry
            view_kwargs = self.route_info["handler_kwargs"]
            view_callable = self.route_info["handler"]
            
            # Execute the view callable and retrieve the http response
            view_callable = convert_to_async_if_needed(view_callable)
            response = await async_view_wrapper(view_callable)(request=self.request, **view_kwargs)
        
        except Exception as e:
            logger.log_raw(
                f'\nError invoking response view for URL "{url}" ',
                level=logger.ERROR,
                custom_color=logger.Fore.YELLOW,
            )
            raise e # reraise exception
        
        # Check and convert the data returned by the view to Http response.
        try:
            response = to_response(response)
        except TypeError as e:
            # The data received from the view cannot be converted to http response.
            raise TypeError(f"Invalid data received from response view for URL '{url}'") from e
        
        return response

    async def get_django_response(self) -> HttpProxyResponse:
        """
        Returns the streaming http response fetched from django server.
        
        Raises:
            MethodNotAllowedError: If the requested method is not allowed for the current request.
            RouteNotFoundError: If the requested url doesn't match any registered routes.
        """
        # create proxy handler
        uses_ipv6 = Meta.get_metadata("DUCK_USES_IPV6")
        django_host, django_port = Meta.get_metadata("DUCK_DJANGO_ADDR")
        
        # Check for errors
        try:
            self.check_errors()
        except RouteNotFoundError as e:
            if is_django_side_url(self.request.path):
                # The request is not registered within Duck but in Django, ignore 404 error.
                pass
            else:
                raise e # reraise error
        
        try:
            proxy_handler = PROXY_HANDLER(
                target_host=django_host,
                target_port=django_port,
                uses_ipv6=uses_ipv6,
                uses_ssl=False,
            ) # build a proxy handler
            
            # Ensure http version is HTTP/1.1
            if "/2" in str(self.request.http_version):
                self.request.http_version = "HTTP/1.1"
            
            # Retrieve the http response from django server.
            streaming_proxy_response = await convert_to_async_if_needed(proxy_handler.get_response)(
                self.request,
                self.request.client_socket,
            )
            
            # Return the http streaming response obtained from django server.
            return streaming_proxy_response
        
        except Exception as e:
            if self.request and hasattr(self.request, "META"):
                self.request.META["DEBUG_MESSAGE"] = f"Bad Gateway: [{django_host}, {django_port}]"
            raise e # Reraise error.

    async def get_middleware_error_response(self, middleware) -> HttpResponse:
        """
        Returns middleware error response.
        """
        return await convert_to_async_if_needed(middleware.get_error_response)(self.request)

    async def get_response(self, request: HttpRequest) -> HttpResponse:
        """
        Returns the full response for a request, with all middlewares and other configurations applied.
        
        Returns:
            HttpResponse: Http response
        """
        response, disable_logging = await ASGI.get_response(request)
        return response
        
    async def process_request(self) -> HttpResponse:
        """
        Processes the http request and returns the appropriate http response.
        """
        self.check_base_errors() # check base errors like request syntax error, etc
        
        # Process request further after confirmation that request has no base errors
        # like RequestSyntaxError, RequestUnsupportedVersionError, etc.

        # Check for middleware errors.
        state, middleware = await self.check_middlewares()
        
        if SETTINGS["MIDDLEWARE_FAILURE_BEHAVIOR"] != "ignore":
            if state == "bad":
                return await self.get_middleware_error_response(middleware)
        
        # Return the appropriate view response.
        response = await self.get_view_response()
        return response
        
    async def process_django_request(self) -> HttpProxyResponse:
        """
        Processes the request and send it to Django proxy for 
        receiving the appropriate http response.
        """
        self.check_base_errors() # check base errors like request syntax error, etc
        
        # Process request further after confirmation that request has no base errors
        # like RequestSyntaxError, RequestUnsupportedVersionError, etc.
        
        django_side_urls_skip_middlewares = SETTINGS["DJANGO_SIDE_URLS_SKIP_MIDDLEWARES"] # skip middlewares for urls registered in Django.
        django_side_url = is_django_side_url(self.request.path)
        duck_explicit_url = is_duck_explicit_url(self.request.path)
        
        if django_side_url:
            # Request is meant to be handled straight by django,
            # Url pattern for this request is only known by Django.
            if not django_side_urls_skip_middlewares:
                # Check all middlewares
                state, middleware = await self.check_middlewares()
                
                if SETTINGS["MIDDLEWARE_FAILURE_BEHAVIOR"] != "ignore":
                    if state == "bad":
                         return await self.get_middleware_error_response(middleware)
            
        else:
            # Check all middlewares
            state, middleware = await self.check_middlewares()
            if SETTINGS["MIDDLEWARE_FAILURE_BEHAVIOR"] != "ignore":
                if state == "bad":
                         return await self.get_middleware_error_response(middleware)
        
        if duck_explicit_url:
            # USE_DJANGO=True but this request is to be handled directly by Duck
            # Request's urlpattern is also known to Django but prefer Duck to handle the request,
            # don't proxy the request to Django server. (only if url is not also django side url)
            if not django_side_url:
                return await self.get_view_response()
        
        # Return the appropriate response by proxying request to Django server first
        return await self.get_django_response()
