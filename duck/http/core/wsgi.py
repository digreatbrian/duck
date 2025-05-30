"""
This module provides the WSGI (Web Server Gateway Interface) for the Duck HTTP server.

WSGI is a specification that describes how a web server communicates with web applications.
This module will define the WSGI callable that the server will use to serve requests.
"""

import socket
import asyncio

from typing import (
    Any,
    Dict,
    Optional,
    Tuple,
    Union,
)

from duck.exceptions.all import (
    SettingsError,
    RouteNotFoundError,
    MethodNotAllowedError,
    RequestError,
    RequestUnsupportedVersionError,
    RequestSyntaxError,
    
)
from duck.http.core.handler import ResponseHandler
from duck.http.core.proxyhandler import (
    HttpProxyResponse,
    BadGatewayError,
)
from duck.http.core.response_finalizer import ResponseFinalizer
from duck.http.request import HttpRequest
from duck.http.request_data import RequestData
from duck.http.response import (
    HttpBadGatewayResponse,
    HttpResponse,
    HttpServerErrorResponse,
    HttpMethodNotAllowedResponse,
    HttpNotFoundResponse,
    HttpBadRequestResponse,
    HttpBadRequestSyntaxResponse,
    HttpUnsupportedVersionResponse,
)
from duck.routes import RouteRegistry
from duck.logging import logger
from duck.meta import Meta
from duck.settings import SETTINGS
from duck.shortcuts import (
    simple_response,
    template_response,
)


# Class for making final adjustments to responses
response_finalizer = ResponseFinalizer()


# Class for sending and logging resoponses
response_handler = ResponseHandler()


# Css style for debug error as html
debug_error_style = """
<style>
  h1 {
    color: #d32f2f; /* Deep red for error text */
  }
  .request-info .inner {
     background-color: #fdf2f2; /* Soft red background for better readability */
     border-radius: 4px;
     padding: 4px 4px;
     list-style: none;
  }
  .request-info .inner li {
    margin-left: 5px;
    color: #d32f2f; /* Deep red for error text */
  }
</style>	
"""
 
def get_debug_error_as_html(exception: Exception, request: Optional = None):
    """
    Returns the exception as html (only if DEBUG=True, else None).
    """
    def escape(content: str):
        """
        Returns escaped html content.
        """
        return content.replace("<", "&lt;").replace(">", "&gt;")
    
    if not SETTINGS["DEBUG"]:
        # return None immediately
        return
    
    # Expand exception  
    exception = logger.expand_exception(exception)
    
    # Make html from exception
    host = None # intialize host
    exception = escape(exception).replace("^\n", "^\n\n").replace("\n", "\n<br>")
    
    if not request:
       body = f"""
       <div class="request-info">
         <h4 class="subheading">Request</h4>
         <ul class="inner">Failed to retreive request metadata.</ul>
       </div><br><div class="exception">{exception}</div>
       """
       body = body + debug_error_style
       return body # return the body and style
    
    else:
      # Retrieve the original host
      if SETTINGS["USE_DJANGO"]:
          # If not real https host set, fallback to http host because this request might have been included inDUCK_EXPLICIT_URLS
          host = request.META.get("REAL_HTTP_HOST") or request.META.get("HTTP_HOST")
      
      else:
          host = request.META.get("HTTP_HOST")
      
      body = f"""
      <div class="request-info">
        <h4 class="subheading" >Request</h4>
        <ul class="inner">
          <li><p>Path: {request.path}</p>
          <li><p>Method: {request.method}</p>
          <li><p>Host: {host}</p>
          <li><p>HTTP-Version: {request.http_version if request.request_store.get("h2_handling") != True else "HTTP/2"}</p>
          <li><p>Content-Length: {request.content_obj.size}</p>
        </ul>
      </div><br><div class="exception">{exception}</div>
      """
      
      return body + debug_error_style


def get_server_error_response(exception: Exception, request: Optional = None):
    """
    Returns HttpServerError Response for the provided exception.
    """
    from duck.contrib.responses import simple_response, template_response
    
    if request:
        request.META["DEBUG_MESSAGE"] = f"Internal Server Error: {request.path}"
    
    if SETTINGS["DEBUG"]:
        body = get_debug_error_as_html(exception, request)
        response = template_response(
            HttpServerErrorResponse,
            body=body,
        )
        return response
    else:
        response = simple_response(HttpServerErrorResponse)


def get_bad_gateway_error_response(exception: Optional[Exception], request: Optional = None):
    """
    Returns the appropriate Bad Gateway response.

    Args:
            exception (Optional[Exception]): The exception which might have caused this.
            The exception may be included in response.
            request (Optional): The current http request.
    """
    from duck.contrib.responses import simple_response, template_response
    
    if request:
        request.META["DEBUG_MESSAGE"] = f"Bad Gateway: {request.path}"
    
    if SETTINGS["DEBUG"]:
        body = get_debug_error_as_html(exception, request)
        response = template_response(
            HttpBadGatewayResponse,
            body=body,
        )
    else:
        response = simple_response(HttpBadGatewayResponse)
    return response


def get_404_error_response(request: HttpRequest):
    """
    Returns HttpNotFoundError Response for the request.
    """
    if request:
        request.META["DEBUG_MESSAGE"] = f"Not Found: {request.path}"
    
    if SETTINGS["DEBUG"]:
        body = f'<p>Specified URI not found: {request.path}</p>'
        if SETTINGS["USE_DJANGO"]:
            body += "<p>It seems like USE_DJANGO=True in settings, maybe this url is registered and only known to Django.</p>"
            body += "<p>You may add this url to DJANGO_SIDE_URLS if that is the case.</p>"
        
        # Add a list of registered routes
        body += "<h3>Duck tried the following routes</h3>"
        body += "<div class='registered-routes'>"
        
        for route, info in RouteRegistry.url_map.items():
            name = list(info.items())[0][0]
            
            # Replace < and > in route with allowed html signs (if present)
            route = route.replace('>', "&gt;").replace('<', "&lt;")
            
            body += f"""\n
            <div class='route' >
                <strong>{route}</strong> [name='{name}']
            </div>
            """
        
        # Close the div tag and add style
        body += "</div>"
        style = """
        <style>
           /* Other styles are derived from base_template_response.html */
            :root {
                --primary-color: #FF8C00;
            }
           div.registered-routes {
               border-radius: var(--border-radius);
               background-color: #fdf2f2; /* Soft red background for better readability */
               padding: 5px;
           }
           
            div.registered-routes .route {
                margin-top: 2px;
                color: var(--text-color);
            }
        </style>
        """
        body += style
        
        # Create an http template response
        response = template_response(
            HttpNotFoundResponse,
            body=body,
        )
    else:
        body = None
        response = simple_response(HttpNotFoundResponse, body=body)
    return response


def get_method_not_allowed_error_response(request: HttpRequest, route_info: Optional[Dict[str, Any]] = None):
    """
    Returns HttpMethodNotAllowed Response for the request.
    
    Args:
        request (HttpRequest): The http request.
        route_info (Optional[Dict[str, Any]]): The route info for the request obtained by RouteRegistry.
    """
    if request:
        request.META["DEBUG_MESSAGE"] = f"Method Not Allowed: {request.method}"
    
    if SETTINGS["DEBUG"]:
        if route_info:
            body = f'<p>Specified Method not allowed</p><div class="allowed-methods"> Allowed Methods: {[m.upper() for m in route_info["methods"]]}'
        else:
            body = "<p>Specified Method not allowed</p>"
        response = template_response(
            HttpMethodNotAllowedResponse,
            body=body,
       )
    else:
        body = None
        response = simple_response(HttpMethodNotAllowedResponse, body=body)
    return response


def get_bad_request_error_response(exception: Exception, request: Optional[HttpRequest] = None):
    """
    Returns HttpBadRequest Response for the request.
    
    Args:
        exception (Exception): The appropriate exception.
        request (Optional[HttpRequest]): The http request.
    """
    if request:
        request.META["DEBUG_MESSAGE"] = f"Bad Request: {request.path}"
    
    response_cls = HttpBadRequestResponse
    body = (
        "<p>Bad request, there is an error in request.</p><p>"
        "You might need to reconstruct request in right format</p>"
    )
    ref = f"<p>Ref: {exception}</p>"
    
    if isinstance(exception, RequestSyntaxError):
        response_cls = HttpBadRequestSyntaxResponse
        body = "<p>Bad request syntax.</p><p>You might need to reconstruct request in right format</p>"
        
        if request:
            request.META["DEBUG_MESSAGE"] = f"Bad Request Syntax: {request.path}"

    elif isinstance(exception, RequestUnsupportedVersionError):
        response_cls = HttpUnsupportedVersionResponse
        body = "<p>Unsupported http version.</p><p>You might need to switch to supported protocol.</p>"
        if request:
            request.META["DEBUG_MESSAGE"] = f"Unsupported HTTP Version: {request.http_version}"
    else:
        # General request error
        if "'utf-8' codec can't decode byte" in str(exception) and not SETTINGS['ENABLE_HTTPS']:
            # This might be a client sending https traffic to our http server
            response_cls = HttpBadRequestResponse
            body = "<p>Bad request, there is an error in request.</p><p>This might be a client sending https encrypted data to our http server.</p>"
            if request:
                request.META["DEBUG_MESSAGE"] = "Bad Request: Client might be trying to send HTTPs traffic to our HTTP server"
    
    if SETTINGS["DEBUG"]:
        response = template_response(response_cls, body=body + ref)
    else:
        body = None
        response = simple_response(response_cls, body=body)
    return response


class WSGI:
    """
    Web Server Gateway Interface for the Duck HTTP server

    Notes:
                - The WSGI callable is the entry point for the server to handle requests.
                - The WSGI callable will be called for each incoming request.
                - The WSGI callable will handle the request and send the response to the client.
                - The WSGI callable will be called with the following arguments:
                                - application: The Duck application instance.
                                - client_socket: The client socket object.
                                - client_address: The client address tuple.
                                - request_data: The raw request data from the client.
                - The WSGI is also responsible for sending request to remote servers like Django for processing.

                Implement methods get_request, start_response and __call__ to create your custom WSGI callable.

    """

    def __init__(self, settings: Dict[str, Any]):
        self.settings = settings
        self.response_finalizer = response_finalizer
        self.response_handler = response_handler

    @staticmethod
    def get_request(
        client_socket: socket.socket,
        client_address: Tuple[str, int],
        request_data: RequestData,
    ) -> HttpRequest:
        """
        Construct a Request object from the data received from the client

        Args:
                client_socket (socket.socket): The client socket object.
                client_address (tuple): The client address tuple.
                request_data (RequestData): The request data object
                     
        Returns:
            HttpRequest: The request object
        """
        from duck.settings.loaded import REQUEST_CLASS

        request_class = REQUEST_CLASS

        if not issubclass(request_class, HttpRequest):
            raise SettingsError(
                f"REQUEST_CLASS set in settings.py should be an instance of Duck HttpRequest not {request_class}"
            )
        
        request = request_class(
            client_socket=client_socket,
            client_address=client_address,
        )
        
        # Parse request data
        request.parse(request_data)
        
        return request

    def finalize_response(self,
        response,
        request: Optional[HttpRequest] = None):
        """
        Finalizes response by adding final touches and sending response to client.
        """
        try:
            self.response_finalizer.finalize_response(response, request)
        except Exception as e:
            logger.log_exception(e)

    def send_response(
        self,
        response,
        client_socket: socket.socket,
        request: Optional[HttpRequest] = None,
        disable_logging: bool = False,
    ):
        """
        Sends response to client.
        """
        self.response_handler.send_response(
            response,
            client_socket,
            request=request,
            disable_logging=disable_logging,
         )

    def apply_middlewares_to_response(self, response, request):
        """
        Apply middlewares to the final response starting from the failed middleware or
        last middleware in list to the first middlewares. Its just like reversing middleware
        list and iterating through each and every one of them.
        """
        from duck.settings.loaded import MIDDLEWARES

        middlewares = MIDDLEWARES
        failed_middleware = request.META.get("FAILED_MIDDLEWARE")
        
        if failed_middleware:
            # strip other middlewares if the request didn't get to reach them or come through any of them
            index = middlewares.index(failed_middleware)
            middlewares = middlewares[:index]

        for middleware in reversed(middlewares):
            middleware.process_response(response, request)
    
    def django_apply_middlewares_to_response(self, response: HttpProxyResponse, request):
        """
        Applies middlewares to the final http proxy response.
        """
        if not SETTINGS["DJANGO_SIDE_URLS_SKIP_MIDDLEWARES"]:
            # If request reached django server server and we got a response,
            # this means all middlewares were successful.
            self.apply_middlewares_to_response(response, request)
    
    def get_response(self, request: HttpRequest) -> Tuple[HttpResponse, bool]:
        """
        Returns the full response for a request, with all middlewares and other configurations applied.
        
        Returns:
            Tuple[HttpResponse, bool]: Http response and a boolean whether to log the response to the console.
        """
        from django.db import close_old_connections
        from duck.http.core.processor import RequestProcessor
        
        processor = None # initialize request processor
        response = None
        disable_logging = False
        
        try:
            processor = RequestProcessor(request)
            
            if SETTINGS["USE_DJANGO"]:
                # Obtain the http response for the request
                response: HttpProxyResponse = processor.process_django_request()
                
                # Apply middlewares in reverse order
                self.django_apply_middlewares_to_response(response, request)
            
            else:
                # Obtain the http response for the request
                response = processor.process_request()
                
                # Apply middlewares in reverse order
                self.apply_middlewares_to_response(response, request)
                
        except RouteNotFoundError:
            # The request url cannot match any registered routes.
            response = get_404_error_response(request)
            
        except MethodNotAllowedError:
            # The requested method not allowed for the current route.
            route_info = None
            try:
                if processor:
                    # Obtain the request route info
                    route_info = processor.route_info
            except:
                pass
            
            # Retrieve the method not allowed error response.
            response = get_method_not_allowed_error_response(request, route_info=route_info)
            
        except RequestError as e:
            # The request has some errors
            # Retrieve the bad request error response.
            response = get_bad_request_error_response(e, request)
            
        except Exception as e:
            if isinstance(e, BadGatewayError):
                # Retrieve the bad gateway error response
                response = get_bad_gateway_error_response(e, request)
            
            else:
                # Retrieve ther server error response
                response = get_server_error_response(e, request)
                logger.log_exception(e)
            
            # Disable logging as django already logged the response.
            if SETTINGS["USE_DJANGO"]:
                disable_logging = True
        
        # Clean up Django DB connections
        close_old_connections()
        
        # Finalize and return response
        self.finalize_response(response, request)
        
        return (response, disable_logging)
        
    def start_response(self, request: HttpRequest):
        """
        Start the response to the client. This method should be called for handling and sending the response to client.

        Args:
                request (HttpRequest): The request object.
        """
        response, disable_logging = self.get_response(request)
        
        # Send response to client
        self.send_response(
            response,
            request.client_socket,
            request,
            disable_logging=disable_logging,
        )
        
    def __call__(
        self,
        application,
        client_socket: socket.socket,
        client_address: Tuple[str, int],
        request_data: RequestData,
    ) -> Optional[HttpRequest]:
        """
        WSGI Application callable for handling requests

        Notes:
            - This method is wrapped by a decorator (`if_error_log_then_raise`), which handle any errors
            raised within this method.

        Args:
                application (App): The Duck application instance.
                client_socket (socket.socket): The client socket object.
                client_address (tuple): The client address tuple.
                request_data (RequestData): The request data object
                
        Returns:
                HttpRequest: The handled request object.
        """
        from duck.app.app import App
        from duck.app.microapp import MicroApp
        
        # Run Assertations/Checks
        assert application is not None, "Application not provided."
        
        # Check if application is an instance of App or MicroApp
        assert isinstance(
            application,
            (App, MicroApp)), "Invalid application instance provided."
        
        # Check if request data is bytes representing request or tuple containing headers and content/body respectively
        assert isinstance(request_data, RequestData), f'Request data should be an instance of RequestData not "{type(request_data)}"'
        
        try:
            request = self.get_request(
                client_socket,
                client_address,
                request_data,
            )
        except Exception as e:
            # Internal server error
            response = get_server_error_response(e, None)
            
            self.send_response(
                response,
                client_socket,
                request=None,
            )  # send response to client
            raise e  # reraise error so that it will be logged
            
        request.application = application
        request.wsgi = self
        application.last_request = request
        
        # Start sending response
        self.start_response(request)
        
        return request
