"""
Handles the response further after they have been processed.
This includes sending response to client and logging the response.
"""

import socket

from typing import Optional, Union, Callable, Dict

from duck.http.request import HttpRequest
from duck.http.response import (
    BaseResponse,
    HttpResponse,
    StreamingHttpResponse,
)
from duck.logging import logger
from duck.settings import SETTINGS
from duck.utils.dateutils import (
    django_short_local_date,
    short_local_date,
)
from duck.etc.statuscodes import responses
from duck.shortcuts import to_response


# Custom templates for predefined responses
# This is a mapping of status codes to a response generating callable
CUSTOM_TEMPLATES: Dict[int, Callable] = SETTINGS["CUSTOM_TEMPLATES"] or {}


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
    if response.status_code == 101:
        return f"Upgrade: {response.get_header('upgrade', 'unknown')}"
    
    if response.status_code < 300:
        return 
        
    if response.status_code in responses.keys():
        debug_msg, reason = responses[response.status_code]
        
        if request:
            if response.status_code in {301, 302, 307}:
                final_debug_msg = f"{debug_msg}: {request.path} -> {response.get_header('location', 'unknown')}"
            else:
                final_debug_msg = f"{debug_msg}: {request.path}"
        else:
            final_debug_msg = f'{debug_msg}: unknown'
        return final_debug_msg
    return "" # empty string to show no debug msg


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
    
    # Add optional debug message if available
    if debug_message:
        info += reset + debug_message.strip() + "\n"
    else:
        debug_message = get_status_debug_msg(response, request)
        if debug_message:
            info += reset + debug_message + "\n"
    
    # Add the main log information with date, status code, content size, and request info
    info += (
        f"[{django_short_local_date()}] {color}"
        f'"{request.topheader if request else ""}" {response.status_code} '
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
    
    if request and request.client_address:
        addr = request.client_address 
    
    info = (
        f'[{short_local_date()}] {color}"{request.topheader if request else ""}" '
        f"{response.content_obj.size}{reset}")
    
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
    ) -> None:
        """
        Sends raw data directly to a client socket.

        Args:
            data (bytes): The data to be sent in bytes.
            client_socket (socket.socket): The client socket object that will receive the data.
            suppress_errors (bool): If True, suppresses any errors that occur during the sending process. Defaults to False.
        
        Returns:
            bool: Whether the data has been sent or None otherwise (usefull if suppress_errors=True)
            
        Raises:
            BrokenPipeError: If the connection is broken during data transmission.
            Exception: Any other exceptions that occur during the sending process.
        """
        try:
            client_socket.sendall(data)
            return True
        except (BrokenPipeError, Exception) as e:
            if not suppress_errors:
                raise e  # Re-raises the error if suppression is not enabled.
    
    def _send_response(
        self,
        response: Union[BaseResponse, HttpResponse],
        client_socket: socket.socket,
        suppress_errors: bool = False,
    ):
       """Explicitly sends an HTTP/1 response to the client socket.
        
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
    
    def send_h2_data(self, h2_connection, stream_id, data):
        """Sends data in chunks according to the max frame size of HTTP/2."""
        # Max frame size allowed (default is 16KB)
        max_frame_size = h2_connection.max_outbound_frame_size
    
        # Send data in chunks based on the max frame size
        for i in range(0, len(data), max_frame_size):
            chunk = data[i: i + max_frame_size]
            h2_connection.send_data(stream_id=stream_id, data=chunk)
    
    def _send_http2_response(
        self,
        response: Union[BaseResponse, HttpResponse],
        client_socket: socket.socket,
        stream_id: int,
        suppress_errors: bool = False,
    ) -> Optional[bool]:
        """Explicitly sends an HTTP/2 response to the H2Connection.
        
        Args:
            response (Union[BaseResponse, HttpResponse]): The HTTP response object containing the response data.
            client_socket (socket.socket): The client socket object to which the response will be sent.
            stream_id (int): Integer for representing stream (according to HTTP/2)
            suppress_errors (bool): If True, suppresses any errors that occur during the sending process. Defaults to False.
         
        Returns:
            bool: Whether the response has been sent or None otherwise
            
        Raises:
            Exception: If there is an error during the data sending process (e.g., socket errors), unless suppressed.
        """
        from h2.connection import ConnectionState
        
        try:
            h2_connection = client_socket.h2_connection
            
            if h2_connection.state_machine.state == ConnectionState.CLOSED:
                return
            
            # Send headers first according HTTP/2
            headers = [
                (header.lower(), value) for header, value in response.headers.items()
            ]
            
            # Add status line/topheader to headers
            headers.insert(0, (":status", str(response.status_code)))
            
            # Send headers alongside with stream ID according to HTTP/2
            h2_connection.send_headers(stream_id=stream_id, headers=headers)
            
            # Now send Content/Body
            if not isinstance(response, StreamingHttpResponse):
                # Send body
                self.send_h2_data(client_socket.h2_connection, stream_id, response.content)
            else:
                content_length = 0
                
                for chunk in response.iter_content():
                     chunk_len = len(chunk)
                     content_length += chunk_len
                     
                     if isinstance(chunk, str):
                         chunk = bytes(chunk, "utf-8")
                     
                     # Send chunk
                     self.send_h2_data(client_socket.h2_connection, stream_id, chunk)
                
                # Set a custom content size for streaming responses, which may not match the actual size 
                # of the current content. This size represents the correct total size of the content 
                # after being fully sent to the client. Setting this enables accurate logging of 
                # the content size.
                response.content_obj.set_fake_size(content_length)
            
            # Mark response as complete
            h2_connection.end_stream(stream_id)

        except Exception as e:
            if not suppress_errors:
                raise e  # Re-raises the error if suppression is not enabled.
        
        return True
        
    def send_response(
        self,
        response: Union[BaseResponse, HttpResponse],
        client_socket: socket.socket,
        request: Optional[HttpRequest] = None,
        disable_logging: bool = False,
        suppress_errors: bool = False,
    ) -> None:
        """
        Sends an HTTP response to the client socket, optionally logging the response.

        Args:
            response (Union[BaseResponse, HttpResponse]): The HTTP response object containing the response data.
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
        # Check if a custom template is configured for this response
        
        # Return the http response object.
        if request and str(request.method).upper() == "HEAD":
            # Reset content
            request.set_content(b"", auto_add_content_headers=True)
            
        if not SETTINGS["DEBUG"]:
            # Only enable custom t9emplates in production
            if response.status_code in CUSTOM_TEMPLATES:
                response_callable = CUSTOM_TEMPLATES[response.status_code]
                if not callable(response_callable):
                    raise TypeError(f"Callable required for custom template corresponding to status code of '{response.status_code}' ")
                
                # Parse parameters and obtain the custom template response.
                new_response = response_callable(
                    current_response=response,
                    request=request,
                )
                try:
                    new_response = to_response(new_response) # convert or check the validity of the custom response.
                except TypeError:
                    # The value returned by response_generating_callable is not valid
                    raise TypeError(f"Invalid data returned by the custom template callable corresponding to status code '{response.status_code}' ")
                response = new_response # set new response
        
        # Explicitly send response
        if hasattr(client_socket, "h2_handling") and client_socket.h2_handling:
            stream_id = request.request_data.stream_id
            cancel_streams = client_socket.h2_cancel_streams
            
            for cancel_stream_id in cancel_streams:
                if stream_id == cancel_stream_id:
                    # Stream has been cancelled/doesn't need a response at the moment
                    cancel_streams.discard(stream_id) # remove stream id to cancel because we are doing it now by statement 'return'
                    return
            
            if not client_socket.h2_keep_connection:
                # Keeping connection to client has been stopped/cancel, not necessary to continue
                cancel_streams.clear()
                return
           
            # Check if we are still connected
            h2_connection = client_socket.h2_connection
            
            # Send response
            if not self._send_http2_response(
               response,
               client_socket,
               stream_id=stream_id,
               suppress_errors=suppress_errors,
               ):
               # Response not send, connection is closed perhaps
               return
               
        else:
            try:
                self._send_response(response, client_socket, suppress_errors=suppress_errors)
            except (BrokenPipeError, ConnectionResetError):
                # Client disconnected
                return
                
        # Log response (if applicable)
        if not disable_logging:
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
