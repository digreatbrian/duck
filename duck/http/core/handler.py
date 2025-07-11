"""
Handles the response further after they have been processed.
This includes sending response to client and logging the response.
"""
import ssl
import time
import socket

from typing import (
    Optional,
    Union,
    Callable,
    Dict,
    Type,
    List,
)

from duck.http.request import HttpRequest
from duck.etc.statuscodes import responses
from duck.http.response import (
    BaseResponse,
    HttpResponse,
    StreamingHttpResponse,
)
from duck.contrib.sync import convert_to_async_if_needed
from duck.settings import SETTINGS
from duck.logging import logger
from duck.utils.dateutils import (django_short_local_date, short_local_date,)


def get_status_code_debug_color(status_code: int) -> str:
    """
    Returns the respective color for the debug message of the status code.
    """
    status = str(status_code)
    
    if status.startswith("1") or status.startswith("2"):
        # informational or success status code respectively
        color = logger.Fore.GREEN
    
    elif status.startswith("3"):
        # Redirectional
        color = logger.Fore.CYAN
    
    elif status.startswith("4"):
        # Client Error
        color = logger.Fore.YELLOW
        
        if status == "403":
            # Forbidden
            color = logger.Fore.RED
    else:
        # Internal Server Error
        color = logger.Fore.RED
        if status == "500":
            color = logger.Fore.MAGENTA
    return color


def get_status_debug_msg(response: HttpResponse, request: HttpRequest) -> Optional[str]:
    """
    Returns a debug message corresponding to an HTTP status code.

    This function is typically used when a request-response lacks an attached
    debug message, but the response carries special meaning that warrants 
    additional debugging information based on the status code.

    Args:
        response (HttpResponse): The HTTP response for which the debug message is required.
        request (HttpRequest): The HTTP request associated with the status code.

    Returns:
        str: A debug message that provides context or explanation for the given status code.
    """
    # exceptional status code that doesnt require debug messages
    final_debug_msg = ""
    
    if response.status_code == 101:
        final_debug_msg += f"Upgrade: {response.get_header('upgrade', 'unknown')}"
        return final_debug_msg
    
    if response.status_code < 300:
        return final_debug_msg
        
    if response.status_code in responses.keys():
        debug_msg, reason = responses[response.status_code]
        
        if request:
            if response.status_code in {301, 302, 307}:
                final_debug_msg += f"{debug_msg}: {request.path} -> {response.get_header('location', 'unknown')}"
            else:
                final_debug_msg += f"{debug_msg}: {request.path}"
        else:
            final_debug_msg += f'{debug_msg}: unknown'
    return final_debug_msg


def get_django_formatted_log(
    response: HttpResponse,
    request: Optional[HttpRequest] = None,
    debug_message: str = "",
) -> str:
    """
    Returns a log message formatted similarly to Django logs with color support for various HTTP statuses.

    Args:
        response (HttpResponse): The HTTP response object.
        request (Optional[HttpRequest]): The HTTP request object. Optional, used for adding more detailed log information.
        debug_message (str): A custom debug message to append to the log. Defaults to an empty string.

    Returns:
        str: The formatted log message with color codes based on the HTTP status.
    
    The log format includes:
     - HTTP status code, with color changes based on success, client errors, redirection, or server errors.
     - Optional request path for 500 errors.
     - Optional debug message if provided.
     - Support for redirections with status codes 301 and 307.
    """
    # Initialize variables
    info = ""
    reset = logger.Style.RESET_ALL
    color = get_status_code_debug_color(response.status_code)
    bold_start = "\033[1m"
    bold_end = "\033[0m"
    h2_handling = False
    
    if request and request.request_store.get("h2_handling") == True:
        h2_handling = True
    
    # Add optional debug message if available
    if debug_message:
        info += reset + debug_message.strip() + "\n"
    else:
        debug_message = get_status_debug_msg(response, request)
        if debug_message:
            info += reset + debug_message + "\n"
    
    # Add the main log information with date, status code, content size, and request info
    topheader = request.topheader if request else ""
    
    if topheader and h2_handling:
        meth, path, httpversion = topheader.split(' ', 2)
        topheader = " ".join([meth.strip(), path.strip(), "HTTP/2"])
        
    info += (
        f"[{django_short_local_date()}] {color}"
        f'"{topheader}" {response.status_code} '
        f"{response.content_obj.size}"
    )
    return info + reset  # Restore default color


def get_duck_formatted_log(
    response: HttpResponse,
    request: Optional[HttpRequest] = None,
    debug_message: str = "",
) -> str:
    """
    This returns default duck formatted log with color support.

    Args:
        response (HttpResponse): The http response object.
        request (Optional[HttpRequest]): The http request object.
        debug_message (str): Debug message to add to log.
    """
    info = ""
    reset = logger.Style.RESET_ALL
    color = get_status_code_debug_color(response.status_code)
    addr = ("unknown", "unknown")
    h2_handling = False
    
    if request and request.request_store.get("h2_handling") == True:
        h2_handling = True
    
    if request and request.client_address:
        addr = request.client_address
    
    topheader = request.topheader if request else ""
    
    if topheader and h2_handling:
        meth, path, httpversion = topheader.split(' ', 2)
        topheader = " ".join([meth.strip(), path.strip(), "HTTP/2"])
        
    info = (
        f'[{short_local_date()}] {color}"{topheader}" '
        f"{response.content_obj.size}"
    )
    
    info += f"\n  {reset}├── ADDR {list(addr)} "
    
    if not debug_message:
        # Obtain debug message if not present.
        debug_message = get_status_debug_msg(response, request)
        
    if debug_message:
        info += f"\n  ├── {response.payload_obj.status_message} [{response.payload_obj.status_code}] "
        info += f"\n  {reset}└── {debug_message} "
    else:
        info += f"\n  {reset}└── {response.payload_obj.status_message} [{response.payload_obj.status_code}] "
    
    return info + reset  # Restore default color (default)


def log_response(
    response: Union[BaseResponse, HttpResponse],
    request: Optional[HttpRequest] = None,
    debug_message: str = "",
) -> None:
    """
    Logs a response to the console.

    Args:
        response (Union[BaseResponse, HttpResponse]): The http response object.
        request (Optional[Request]): The http request object.
        debug_message (str): Message to display along the response, usually middleware error debug message.
    """
    logdata = ""
    
    if SETTINGS["USE_DJANGO"]:
        if SETTINGS['PREFERRED_LOG_STYLE'] == "duck":
            logdata = get_duck_formatted_log(response, request, debug_message)
            # Add newline to separate requests for duck formatted logs
            logdata += "\n"  
        else:
            logdata = get_django_formatted_log(response, request, debug_message)
    else:
        if SETTINGS['PREFERRED_LOG_STYLE'] == "django":
            logdata = get_django_formatted_log(response, request, debug_message)
        else:
            logdata = get_duck_formatted_log(response, request, debug_message)
            # Add newline to separate requests for duck formatted logs
            logdata += "\n"  
    
    # Log response, use_colors=False to because logdata already has colors
    logger.log_raw(logdata, use_colors=False)


class ResponseHandler:
    """
    Handles sending processed responses to clients via socket communication.
    This class contains methods for sending raw data and HTTP responses, 
    along with optional error handling and logging.
    """

    def send_data(
        self,
        data: bytes,
        client_socket: socket.socket,
        suppress_errors: bool = False,
        ignore_error_list: List[Type[Exception]] = [ssl.SSLError, BrokenPipeError, OSError],
    ) -> None:
        """
        Sends raw data directly to a client socket.

        Args:
            data (bytes): The data to be sent in bytes.
            client_socket (socket.socket): The client socket object that will receive the data.
            suppress_errors (bool): If True, suppresses any errors (errors not in `ignore_error_list`) that occur during the sending process. Defaults to False.
            ignore_error_list (List[Type[Exception]]): List of error classes to ignore when raised during data transfer.
        
        Returns:
            bool: Whether the data has been sent or None otherwise (usefull if suppress_errors=True)
            
        Raises:
            BrokenPipeError: If the connection is broken during data transmission.
            Exception: Any other exceptions that occur during the sending process.
        """
        try:
            client_socket.sendall(data)
            return True
        
        except Exception as e:
            if any([isinstance(e, exc) for exc in ignore_error_list]):
                return
                    
            if not suppress_errors:
                raise e  # Re-raises the error if suppression is not enabled.
                
    async def async_send_data(
        self,
        data: bytes,
        client_socket: socket.socket,
        suppress_errors: bool = False,
        ignore_error_list: List[Type[Exception]] = [ssl.SSLError, BrokenPipeError, OSError],
    ) -> None:
        """
        Asynchronously sends raw data directly to a client socket.

        Args:
            data (bytes): The data to be sent in bytes.
            client_socket (socket.socket): The client socket object that will receive the data.
            suppress_errors (bool): If True, suppresses any errors (errors not in `ignore_error_list`) that occur during the sending process. Defaults to False.
            ignore_error_list (List[Type[Exception]]): List of error classes to ignore when raised during data transfer.
        
        Returns:
            bool: Whether the data has been sent or None otherwise (usefull if suppress_errors=True)
            
        Raises:
            BrokenPipeError: If the connection is broken during data transmission.
            Exception: Any other exceptions that occur during the sending process.
        """
        try:
            await convert_to_async_if_needed(client_socket.sendall)(data)
            return True
        
        except Exception as e:
            if any([isinstance(e, exc) for exc in ignore_error_list]):
                return
                    
            if not suppress_errors:
                raise e  # Re-raises the error if suppression is not enabled.
                
    def send_http2_response(
        self,
        response: Union[BaseResponse, HttpResponse],
        stream_id: int,
        client_socket: socket.socket,
        request: Optional[HttpRequest] = None,
        disable_logging: bool = False,
        suppress_errors: bool = False,
    ) -> None:
        """
        Sends an HTTP/2 response to the H2Connection.
        
        Args:
            response (Union[BaseResponse, HttpResponse]): The HTTP response object containing the response data.
            stream_id (int): The target H2 stream ID.
            client_socket (socket.socket): The client socket object to which the response will be sent.
            request (Optional[HttpRequest]): The request object associated with the response. Used for logging and debugging purposes.
            disable_logging (bool): If True, disables logging of the response. Defaults to False.
            suppress_errors (bool): If True, suppresses any errors that occur during the sending process (only sending data). Defaults to False.

        Raises:
            Exception: If there is an error during the data sending process (e.g., socket errors), unless suppressed.
        
        This method calls `send_data` to transmit the raw response data to the client and 
        performs logging if `disable_logging` is False. If the request object contains 
        debug information or failed middleware details, they are included in the logs.
        """
        if not hasattr(client_socket, 'h2_protocol'):
            raise AttributeError("The provided socket seem to have no associated HTTP/2 connection, socket should have attribute `h2_protocol` set.")
        
        if request and request.request_store.get("h2_handling") == False:
            raise ValueError("The provided socket seem to have HTTP/2 connection, but the key `h2_handling` in `request.request_store` is False.")
        
        protocol = client_socket.h2_protocol
        
        # Send response according to H2 Protocol
        protocol.send_response(
            response,
            stream_id,
            request,
            disable_logging,
            suppress_errors,
        )
        
    async def async_send_http2_response(
        self,
        response: Union[BaseResponse, HttpResponse],
        stream_id: int,
        client_socket: socket.socket,
        request: Optional[HttpRequest] = None,
        disable_logging: bool = False,
        suppress_errors: bool = False,
    ) -> None:
        """
        Asynchronously sends an HTTP/2 response to the H2Connection.
        
        Args:
            response (Union[BaseResponse, HttpResponse]): The HTTP response object containing the response data.
            stream_id (int): The target H2 stream ID.
            client_socket (socket.socket): The client socket object to which the response will be sent.
            request (Optional[HttpRequest]): The request object associated with the response. Used for logging and debugging purposes.
            disable_logging (bool): If True, disables logging of the response. Defaults to False.
            suppress_errors (bool): If True, suppresses any errors that occur during the sending process (only sending data). Defaults to False.

        Raises:
            Exception: If there is an error during the data sending process (e.g., socket errors), unless suppressed.
        
        This method calls `send_data` to transmit the raw response data to the client and 
        performs logging if `disable_logging` is False. If the request object contains 
        debug information or failed middleware details, they are included in the logs.
        """
        if not hasattr(client_socket, 'h2_protocol'):
            raise AttributeError("The provided socket seem to have no associated HTTP/2 connection, socket should have attribute `h2_protocol` set.")
        
        if request and request.request_store.get("h2_handling") == False:
            raise ValueError("The provided socket seem to have HTTP/2 connection, but the key `h2_handling` in `request.request_store` is False.")
        
        protocol = client_socket.h2_protocol
        
        # Send response according to H2 Protocol
        await protocol.async_send_response(
            response,
            stream_id,
            request,
            disable_logging,
            suppress_errors,
        )
        
    def send_response(
        self,
        response: Union[BaseResponse, HttpResponse],
        client_socket: socket.socket,
        request: Optional[HttpRequest] = None,
        disable_logging: bool = False,
        suppress_errors: bool = False,
        strictly_http1: bool = False,
    ) -> None:
        """
        Sends an HTTP response to the client socket, optionally logging the response.

        Args:
            response (Union[BaseResponse, HttpResponse]): The HTTP response object containing the response data.
            client_socket (socket.socket): The client socket object to which the response will be sent.
            request (Optional[HttpRequest]): The request object associated with the response. Used for logging and debugging purposes.
            disable_logging (bool): If True, disables logging of the response. Defaults to False.
            suppress_errors (bool): If True, suppresses any errors that occur during the sending process (only sending data). Defaults to False.
            strictly_http1 (bool): Strictly send response using `HTTP/2`, even if `HTTP/2` is enabled.
            
        Raises:
            Exception: If there is an error during the data sending process (e.g., socket errors), unless suppressed.
        
        This method calls `send_data` to transmit the raw response data to the client and 
        performs logging if `disable_logging` is False. If the request object contains 
        debug information or failed middleware details, they are included in the logs.
        """
        h2_handling = False
        
        if not strictly_http1 and hasattr(client_socket, 'h2_protocol'):
            if request and request.request_store.get('h2_handling') == False:
                pass
            else:
                # Set H2 handling to True
                h2_handling = True
        
        if h2_handling:
            stream_id = request.request_store.get("stream_id") if request else None
        
            if not stream_id:
                raise TypeError(
                    "HTTP/2 appears to be enabled on the provided socket, "
                    "but no 'stream_id' was found in `request.request_store`. "
                    "Use the `send_http2_response` method directly if you're managing the stream manually."
                )
        
            self.send_http2_response(
                response=response,
                stream_id=stream_id,
                client_socket=client_socket,
                request=request,
                disable_logging=disable_logging,
                suppress_errors=suppress_errors,
            )
            
            return # No further processing
        
        # Explicitly send response
        try:
            self._send_response(response, client_socket, suppress_errors=suppress_errors)
        except (BrokenPipeError, ConnectionResetError):
             # Client disconnected
             return
        
        if not disable_logging:
            # Log response (if applicable)
            type(self).auto_log_response(response, request)

    async def async_send_response(
        self,
        response: Union[BaseResponse, HttpResponse],
        client_socket: socket.socket,
        request: Optional[HttpRequest] = None,
        disable_logging: bool = False,
        suppress_errors: bool = False,
        strictly_http1: bool = False,
    ) -> None:
        """
        Asynchronously sends an HTTP response to the client socket, optionally logging the response.

        Args:
            response (Union[BaseResponse, HttpResponse]): The HTTP response object containing the response data.
            client_socket (socket.socket): The client socket object to which the response will be sent.
            request (Optional[HttpRequest]): The request object associated with the response. Used for logging and debugging purposes.
            disable_logging (bool): If True, disables logging of the response. Defaults to False.
            suppress_errors (bool): If True, suppresses any errors that occur during the sending process (only sending data). Defaults to False.
            strictly_http1 (bool): Strictly send response using `HTTP/2`, even if `HTTP/2` is enabled.
            
        Raises:
            Exception: If there is an error during the data sending process (e.g., socket errors), unless suppressed.
        
        This method calls `send_data` to transmit the raw response data to the client and 
        performs logging if `disable_logging` is False. If the request object contains 
        debug information or failed middleware details, they are included in the logs.
        """
        h2_handling = False
        
        if not strictly_http1 and hasattr(client_socket, 'h2_protocol'):
            if request and request.request_store.get('h2_handling') == False:
                pass
            else:
                # Set H2 handling to True
                h2_handling = True
        
        if h2_handling:
            stream_id = request.request_store.get("stream_id") if request else None
        
            if not stream_id:
                raise TypeError(
                    "HTTP/2 appears to be enabled on the provided socket, "
                    "but no 'stream_id' was found in `request.request_store`. "
                    "Use the `send_http2_response` method directly if you're managing the stream manually."
                )
        
            await self.async_send_http2_response(
                response=response,
                stream_id=stream_id,
                client_socket=client_socket,
                request=request,
                disable_logging=disable_logging,
                suppress_errors=suppress_errors,
            )
            
            return # No further processing
        
        # Explicitly send response
        try:
            await self._async_send_response(response, client_socket, suppress_errors=suppress_errors)
        except (BrokenPipeError, ConnectionResetError):
             # Client disconnected
             return
        
        if not disable_logging:
            # Log response (if applicable)
            type(self).auto_log_response(response, request)
            
    @classmethod
    def auto_log_response(cls, response, request):
        """
        Logs a response to the console, considering middleware errors and any other issues. This
        automatically creates debug messages (if applicable).
        
        Notes:
        - Nothing will be logged if response is `None`.
        """
        if response:
            debug_message = ""
            if request and hasattr(request, "META"):
                failed_middleware = request.META.get("FAILED_MIDDLEWARE")
                if failed_middleware and response.status_code != 500:
                    # Do not log debug message for internal server errors (status code 500).
                    debug_message = failed_middleware.debug_message
                else:
                    debug_message = request.META.get("DEBUG_MESSAGE", "")
            
            # Log the response, including debug messages if available
            log_response(
                response,
                request=request,
                debug_message=debug_message,
            )
            
    def _send_response(
        self,
        response: Union[BaseResponse, HttpResponse],
        client_socket: socket.socket,
        suppress_errors: bool = False,
    ):
       """
        Sends an HTTP response to the client socket.
        
        Args:
            response (Union[BaseResponse, HttpResponse]): The HTTP response object containing the response data.
            client_socket (socket.socket): The client socket object to which the response will be sent.
            suppress_errors (bool): If True, suppresses any errors that occur during the sending process. Defaults to False.

        Raises:
            Exception: If there is an error during the data sending process (e.g., socket errors), unless suppressed.
       """
       try:
           if not isinstance(response, StreamingHttpResponse):
                self.send_data(
                    response.raw,
                    client_socket,
                    suppress_errors=False,
                )  # Send the whole response to the client
           else:
                self.send_data(
                    response.payload_obj.raw + b'\r\n\r\n',
                    client_socket,
                    suppress_errors=False,
                )  # Send the response payload
                
                content_length = 0
                
                for chunk in response.iter_content():
                     content_length += len(chunk)
                     
                     if isinstance(chunk, str):
                         chunk = bytes(chunk, "utf-8")
                     
                     self.send_data(
                         chunk,
                         client_socket,
                         suppress_errors=False,
                      )  # Send the whole response to the client.
                      
                # Set a custom content size for streaming responses, which may not match the actual size 
                # of the current content. This size represents the correct total size of the content 
                # after being fully sent to the client. Setting this enables accurate logging of 
                # the content size.
                response.content_obj.set_fake_size(content_length)   
       except Exception as e:
            if not suppress_errors:
                raise e  # Re-raises the error if suppression is not enabled.
    
    async def _async_send_response(
        self,
        response: Union[BaseResponse, HttpResponse],
        client_socket: socket.socket,
        suppress_errors: bool = False,
    ):
       """
       Asynchronously sends an HTTP response to the client socket.
        
        Args:
            response (Union[BaseResponse, HttpResponse]): The HTTP response object containing the response data.
            client_socket (socket.socket): The client socket object to which the response will be sent.
            suppress_errors (bool): If True, suppresses any errors that occur during the sending process. Defaults to False.

        Raises:
            Exception: If there is an error during the data sending process (e.g., socket errors), unless suppressed.
       """
       try:
           if not isinstance(response, StreamingHttpResponse):
                await self.async_send_data(
                    response.raw,
                    client_socket,
                    suppress_errors=False,
                )  # Send the whole response to the client
           else:
                await self.async_send_data(
                    response.payload_obj.raw + b'\r\n\r\n',
                    client_socket,
                    suppress_errors=False,
                )  # Send the response payload
                
                content_length = 0
                
                for chunk in response.iter_content():
                     content_length += len(chunk)
                     
                     if isinstance(chunk, str):
                         chunk = bytes(chunk, "utf-8")
                     
                     await self.async_send_data(
                         chunk,
                         client_socket,
                         suppress_errors=False,
                      )  # Send the whole response to the client.
                      
                # Set a custom content size for streaming responses, which may not match the actual size 
                # of the current content. This size represents the correct total size of the content 
                # after being fully sent to the client. Setting this enables accurate logging of 
                # the content size.
                response.content_obj.set_fake_size(content_length)   
       except Exception as e:
            if not suppress_errors:
                raise e  # Re-raises the error if suppression is not enabled.
