"""
This module provides the WSGI (Web Server Gateway Interface) for the Duck HTTP server.

WSGI is a specification that describes how a web server communicates with web applications.
This module will define the WSGI callable that the server will use to serve requests.
"""
import time
import socket

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
from duck.http.response import HttpResponse
from duck.http.request import HttpRequest
from duck.http.request_data import RequestData
from duck.logging import logger
from duck.contrib.responses.errors import (
    get_server_error_response,
    get_bad_gateway_error_response,
    get_404_error_response,
    get_method_not_allowed_error_response,
    get_bad_request_error_response,
)
from duck.contrib.sync import convert_to_sync_if_needed
from duck.settings import SETTINGS


# Class for making final adjustments to responses
response_finalizer = ResponseFinalizer()


# Class for sending and logging resoponses
response_handler = ResponseHandler()


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
            convert_to_sync_if_needed(self.response_finalizer.finalize_response)(response, request)
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
            convert_to_sync_if_needed(middleware.process_response)(response, request)
    
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
        from duck.http.core.processor import RequestProcessor
        
        processor = None # initialize request processor
        response = None
        disable_logging = False
        tx = time.perf_counter()
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
