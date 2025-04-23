"""
All utilities and tools a server needs to startup.

This module provides the necessary components for initializing and running a server, including 
handling requests, managing timeouts, and logging.
"""
import re
import ssl
import time
import select
import socket
import asyncio
import threading

from typing import Optional, Tuple, Coroutine, Union, Callable

from duck.contrib.responses import (
    simple_response,
    template_response,
)
from duck.http.core.handler import (
    ResponseHandler,
    log_response,
)
from duck.http.core.processor import RequestProcessor
from duck.http.request import HttpRequest
from duck.http.request_data import (
    RawRequestData,
    RequestData,
)
from duck.http.response import (
    HttpRequestTimeoutResponse,
    HttpResponse,
)
from duck.utils.dateutils import (
    django_short_local_date,
    short_local_date,
)
from duck.utils.ssl import is_ssl_data
from duck.utils.sockservers import xsocket
from duck.settings import SETTINGS
from duck.logging import logger
from duck.meta import Meta


# Using raw bytes string for the regex
KEEP_ALIVE_REGEX = rb"(?i)\bConnection\s*:\s*keep\s*-?\s*alive\b"

KEEP_ALIVE_TIMEOUT = SETTINGS["KEEP_ALIVE_TIMEOUT"]

ASYNC_HANDLING = SETTINGS["ASYNC_HANDLING"]

SERVER_POLL = SETTINGS["SERVER_POLL"]

SERVER_BUFFER = SETTINGS["SERVER_BUFFER"]

REQUEST_TIMEOUT = SETTINGS["REQUEST_TIMEOUT"]

CONNECTION_MODE = SETTINGS["CONNECTION_MODE"]

# Class for sending and logging resoponses
response_handler = ResponseHandler()


def call_request_handling_executor(task: Union[threading.Thread, Coroutine]):
    """
    This calls the request handling executor with the provided task (thread or coroutine) and the 
    request handling executor keyword arguments set in settings.py.
    """
    from duck.settings.loaded import REQUEST_HANDLING_TASK_EXECUTOR
    
    REQUEST_HANDLING_TASK_EXECUTOR.execute(task) # execute thread or coroutine.


def get_timeout_error_response(timeout: Optional[Union[int, float]]) -> HttpRequestTimeoutResponse:
    """
    Returns the request timeout error response.
    
    Args:
        timeout (Union[int, float]): The timeout in seconds.
        
    """
    if SETTINGS["DEBUG"]:
        body = "<p>Client sent nothing in expected time it was suppose to!</p>"
        
        if timeout:
            body = "<p>Client sent nothing in expected time it was suppose to!</p><div>Timeout: ({timeout} seconds)</div>"
        
        response = template_response(
            HttpRequestTimeoutResponse,
            body=body,
        )
    else:
        response = simple_response(HttpRequestTimeoutResponse)


class BaseServer:
    """
    BaseServer class containing server definitions.
    """

    poll: float | int = SERVER_POLL
    """Interval pause for server to handle next Request"""

    buffer: int = SERVER_BUFFER
    """Buffer to handle on requests"""

    request_timeout: int = REQUEST_TIMEOUT
    """Time to wait for a request from a client (in seconds)"""

    connection_mode: str = CONNECTION_MODE
    """
    Server preferred connection mode, either keep-alive or close.
    """

    @property
    def running(self):
        return self.__running

    @running.setter
    def running(self, state: bool):
        self.__running = state

    def close_socket(self, sock):
        """
        Shuts down a socket and finally closes it.
        
        Args:
            sock (socket.socket): The socket object.
        """
        try:
            if not self.sock == sock:
                # This is a client socket
                sock.shutdown(socket.SHUT_RDWR)
            else:
                # Skip shutting down server socket, it may cause OSError: [Errno 22] Invalid argument
                pass
        except Exception:
            # Ignore any exception
            pass
        try:
            sock.close()
        except Exception:
            # ignore any exception
            pass
    
    def start_server(self, no_logs: bool = False, domain: str = None):
        """
        Starts HTTP or HTTPS based server.

        Args:
            no_logs (bool, optional): Whether to or not to log messages like `started server on ...` (defaults to False)
            domain (str, optional): Explicit domain that will be logged alongside the log messages.
        """
        host, port = self.addr
        self.sock.bind(self.addr)  # bind socket to (address, port)
        
        # Server setup
        duck_host = domain or Meta.get_metadata("DUCK_SERVER_HOST")
        duck_host = (list(duck_host)[0] if isinstance(duck_host, tuple) else
                     duck_host or "localhost")
        server_url = "https" if self.enable_ssl else "http"
        server_url += f"://{duck_host}:{port}"

        if SETTINGS["DEBUG"]:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        
        if not no_logs:
            if SETTINGS["DEBUG"]:
                logger.log(f"Started Duck Server on {server_url}", level=logger.DEBUG)
            else:
                logger.log(
                    f"Started Duck ProServer on {server_url}\n  ├── PRODUCTION SERVER (domain: {domain or 'Not set'}) \n  "
                    f"└── This is a production server, always stay secure! ",
                     level=logger.DEBUG)
        
        # Listen and set the server in running state
        self.sock.listen(SETTINGS["REQUESTS_BACKLOG"]) # 200 by default
        self.running = True
        
        # listen and accept incoming connections
        while self.running:
            try:
                # Accept incoming connections
                if self.uses_ipv6:
                    self.accept_and_handle_ipv6()
                else:
                    self.accept_and_handle_ipv4()
                # Pause before the next request.
                time.sleep(self.poll) 
            
            except ssl.SSLError as e:
                # Wrong protocol used, e.g. https on http or vice versa
                if not no_logs and (SETTINGS["VERBOSE_LOGGING"] or SETTINGS["DEBUG"]):
                    if "HTTP_REQUEST" in str(e):
                        logger.log(f"Client may be trying to connect with https on http server or vice-versa: {e}", level=logger.WARNING)
            
            except ConnectionResetError:
                pass
        
            except Exception as e:
                if not no_logs:
                    logger.log_exception(e)

    def stop_server(self, log_to_console: bool = True):
        """
        Stops the http(s) server.
        
        Args:
            log_to_console (bool): Log the message that the sever stoped. Defaults to True.
        """
        self.running = False
        bold_start = "\033[1m"
        bold_end = "\033[0m"
        self.close_socket(self.sock)
        
        if log_to_console: # log message indicating server stopped.
            logger.log_raw('\n')
            logger.log(
                f"{bold_start}Duck server stopped!{bold_end}",
                level=logger.INFO,
                custom_color=logger.Fore.MAGENTA,)
            
            # redo socket close to ensure server stopped.
            self.running = False
            self.close_socket(self.sock)
    
    def accept_and_handle_ipv6(self):
        """
        Accepts and handle IPV6 connection.
        """
        sock, (host, port, flowinfo, scopeid)  = self.sock.accept()
        sock = xsocket.from_socket(sock)
        addr = (host, port)
        args = (self.handle_conn, sock, addr, flowinfo, scopeid)
        
        if ASYNC_HANDLING:
            self._start_async_task(*args)
        else:
            self._start_thread(*args)
            
    def accept_and_handle_ipv4(self):
        """
        Accepts and handle IPV4 connection.
        """
        sock, addr = self.sock.accept()
        sock = xsocket.from_socket(sock)
        args = (self.handle_conn, sock, addr)
        
        if ASYNC_HANDLING:
            self._start_async_task(*args)
        else:
            self._start_thread(*args)
        
    def handle_conn(
        self,
        sock: socket.socket,
        addr: Tuple[str, int],
        flowinfo: Optional = None,
        scopeid: Optional = None,
    ) -> None:
        """
        Main entry point to handle new connection (supports both ipv6 and ipv4).

        Args:
            sock (socket.socket): The client socket object.
            addr (Tuple[str, int]): Client ip and port.
            flowinfo (Optional): Flow info if IPv6.
            scopeid (Optional): Scope id if IPv6.
        """
        sock.addr = addr
        try:
            # Receive the full request (in bytes)
            data = self.receive_full_request(sock, self.request_timeout)
        except TimeoutError:
            # For the first request, client took too long to respond.
            self.do_request_timeout(sock, addr)
            return
        
        if not data:
            # Client sent an empty request, terminate the connection immediately
            self.close_socket(sock)
            return
        
        # Process data/request 
        self.process_data(sock, addr, RawRequestData(data))
    
    def process_data(self, sock, addr, request_data: RawRequestData):
        """
        Process and handle the request dynamically
        """
        data = request_data.data if isinstance(request_data, RawRequestData) else request_data.content
        
        if is_ssl_data(data):
            logger.log(
                "Data should be decoded at this point but it seems like its ssl data",
                level=logger.WARNING,
            )
            logger.log(f"Client may be trying to connect with https on http server or vice-versa\n", level=logger.WARNING)
            return
            
        try:
            self.process_and_handle_request(sock, addr, request_data)
        except Exception as e:
            # processing and handling error resulted in an error
            # log the error message
            logger.log_exception(e)
        
        finally:
            keep_alive_re = re.compile(KEEP_ALIVE_REGEX)
            
            # Check if client wants a keep alive connection
            # Only handle keep alive connection if the server supports it.
            if keep_alive_re.search(data.split(b"\r\n\r\n")[0]):  # target headers only
                if self.connection_mode == "keep-alive":
                    # server supports keep alive
                    self.handle_keep_alive_conn(sock, addr)
            
            # Finally close the socket if everything is finished
            self.close_socket(sock)
            
    def handle_keep_alive_conn(
        self,
        sock: socket.socket,
        addr: Tuple[str, int],
    ) -> None:
        """
        Processes and handles keep alive connection.
        """
        
        # Assume the client wants keep alive to run forever until explicitly stated to end it.
        while True:
            try:
                # Receive client request with a timeout.
                data = self.receive_full_request(
                    sock, KEEP_ALIVE_TIMEOUT)
                
                if not data:
                    # Client sent nothing or closed connection
                    # End the keep alive data exchange immediately
                    break
                
                # Process and handle the complete request using appropriate WSGI
                self.process_and_handle_request(sock, addr, RawRequestData(data))
            
            except TimeoutError:
                # Client sent nothing in expected time it was suppose to
                # Close connection immediately
                break
            
            except Exception as e:
                # Encountered an unknown exception, log that exception right away
                logger.log_exception(e)
            
            finally:
                # After every keep alive cycle, check if client still wants to continue with
                # the connection or terminate immediately
                keep_alive_re = re.compile(KEEP_ALIVE_REGEX)
                
                if keep_alive_re.search(data.split(b"\r\n\r\n")[0]):
                    # client seem to like to continue with keep alive connection
                    if self.connection_mode == "keep-alive":
                        # keep connection alive
                        continue
                    break
                else:
                    # Client would like to terminate keep alive connection.
                    break

    def do_request_timeout(
        self,
        sock: socket.socket,
        addr: Tuple[str, int],
        no_logs: bool = False,
    ):
        """
        Sends request timeout response to client and close connection.

        Args:
                sock (socket.socket): Client socket object
                addr (Tuple[str, int]): Client ip address and port.
                no_logs (bool): Whether to log response to console.
        """
        # Send timeout error message to client.
        timeout_response = get_timeout_error_response(timeout=self.request_timeout)
        
        # Send timeout response
        response_handler.send_response(
            timeout_response,
            sock,
            disable_logging=no_logs)
        
        self.close_socket(sock)  # close client socket immediately
        
    def process_and_handle_request(
        self,
        sock: socket.socket,
        addr: Tuple[str, int],
        request_data: RequestData,
    ) -> None:
        """
        This processes the request using WSGI application callable.

        Args:
                sock (socket.socket): Client Socket object
                addr (Tuple): Tuple for ip and port from where this request is coming from, ie Client addr
                request_data (RequestData): The request data object
        """
        from duck.settings.loaded import WSGI as handle_wsgi_request
        handle_wsgi_request(self.application, sock, addr, request_data)

    def receive_data(
        self,
        sock: socket.socket,
        timeout: Union[int, float] = 5,
    ) -> bytes:
        """
        Receives data from the socket but raises a TimeoutError if no data is received within the specified time.

        Args:
                sock (socket.socket): The socket object to receive data from.
                timeout (Union[int, float]): The timeout in seconds to receive data.

        Raises:
                TimeoutError: If no data is received within the specified time.

        Returns:
                bytes: The received data in bytes.
        """
        sock.settimeout(timeout) # apply the timeout.
        data = b""
        
        try:
            # Receive data once
            data = sock.recv(self.buffer)
            return data
        except socket.timeout:
            # No data received within expected timeout.
            raise TimeoutError("No data received within specified timeout")
        
        except Exception:
            # Encountered an unknown exception, return data as it is.
            return data
        
        finally:
            # Reset the timeout.
            sock.settimeout(None)

    def receive_full_request(
        self,
        sock: socket.socket,
        timeout: Union[int, float] = 5,
        stream_timeout: Union[int, float] = .1,
     ) -> bytes:
        """
        Receives the complete request data from the socket.
        
        Args:
                sock (socket.socket): The socket object
                timeout (Union[int, float]): Timeout in seconds to receive the first part of the data.
                stream_timeout (Union[int, float]):
                    The timeout in seconds to receive the next stream of
                    bytes after the first part has been received. Default to 0.1 for instant data streaming.
        
        Raises:
                TimeoutError: If no data is received within the first timeout (not stream timeout).

        Returns:
                bytes: The received data in bytes.
        """
        try:
            # Receive the first part of data
            data = self.receive_data(sock, timeout)
        
        except ConnectionResetError:
            # Connection was reset whilst receiving data, return empty bytes
            return b""
        
        except TimeoutError as e:
            # No data was received within the timeout, returm empty bytes
            return b""
        
        except Exception:
            # Unknown exception, return empty bytes
            return b""
        
        if data:
            # First part of data is not empty
            while True:
                try:
                    # Receive data with a stream timeout
                    more_data = self.receive_data(sock, stream_timeout)
                    data += more_data
                    if not data:
                        # Data received is empty, this may mean the client is done sending.
                        break
                
                except TimeoutError as e:
                    # Client sent nothing within the stream timeout, ignore and stop receiving more data
                    break
                
                except Exception:
                    # Unknown exception, ignore and stop receiving more data
                    break
        
        # Return the received data
        return data
    
    def is_socket_closed(self, sock: socket.socket, timeout: float=.1) -> bool:
        """Check if a client socket has closed the connection.
        
        Note:
            - This may hang if the connected endpoint doesn't send anything. Utilize socket.settimeout to counter this.

        Args:
            sock (socket.socket): The client socket.

        Returns:
            bool: True if the socket is closed, False otherwise.
        """
        try:
            # Use select to check if the socket is readable
            r, _, _ = select.select([sock], [], [], 0)
            if r:
                data = sock.recv(1, socket.MSG_PEEK)
                if len(data) == 0:
                    return True
            return False
        except socket.error:
            return True
        except ValueError or OSError:
            # likely socket is closed
            return True
    
    def _start_thread(
        self,
        target: Callable,
        sock: socket.socket,
        addr: Tuple[str, int],
        flowinfo=None,
        scopeid=None,
     ) -> None:
        """
        Starts a new thread for handling connections.

        Args:
            target (Callable): The target function to run in the thread.
            sock (socket.socket): The socket object representing the connection.
            addr (Tuple[str, int]): The client ip and port
            flowinfo (int, optional): Flow information for IPv6. Defaults to None.
            scopeid (int, optional): Scope ID for IPv6. Defaults to None.
        """
        args = [sock, addr]
        ip, port = addr
        
        if flowinfo is not None and scopeid is not None:
            args.extend([flowinfo, scopeid])

        client_thread = threading.Thread(
            target=target,
            args=args,
            name=f"client-{ip}@{port}",
        ) # create the request handling thread with custom name
        
        # Execute request handling thread
        call_request_handling_executor(client_thread)

    def _start_async_task(
        self,
        target: Callable,
        sock: socket.socket,
        addr: Tuple[str, int],
        flowinfo=None,
        scopeid=None,
     ) -> None:
        """
        Start a new asynchronous task for handling connections.

        Args:
            target (Callable): The target function to run in the thread.
            sock (socket.socket): The socket object representing the connection.
            addr (Tuple[str, int]): The client ip and port
            flowinfo (int, optional): Flow information for IPv6. Defaults to None.
            scopeid (int, optional): Scope ID for IPv6. Defaults to None.
        """     
        args = [sock, addr]
        
        if flowinfo is not None and scopeid is not None:
            args.extend([flowinfo, scopeid])
        
        async def inner_client_task():
            # inner function to request handling task execution
            target(*args)
            
        async def client_task(): # create the asynchronous request handling coroutine.
            # entry function to task execution
            await inner_client_task()
        
        # Execute request handling coroutine
        call_request_handling_executor(client_task)


class BaseMicroServer:
    """
    BaseMicroServer class containing definitions for micro application server.
    
    This class is the base definition of a micro application server.
    """

    def set_microapp(self, microapp):
        """Sets the target micro application for this server instance."""
        from duck.app.microapp import MicroApp

        if not isinstance(microapp, MicroApp):
            raise ValueError(
                f"MicroApp instance expected, received {type(micropp)} instead."
            )
        self.microapp = microapp # set the micro application instance

    def process_and_handle_request(
        self,
        sock: socket.socket,
        addr: Tuple[str, int],
        request_data: RequestData,
    ) -> None:
        """
        Processes and handles the request.

        Args:
            sock (socket.socket): The target client socket.
            addr (Tuple): The client address and port.
            request_data (RequestData): The full request data object.
        """
        from duck.shortcuts import to_response
        from duck.settings.loaded import WSGI
        
        try:
            request = HttpRequest(
                client_socket=sock,
                client_address=addr,
            ) # create an http request instance.
            
            # Parse request data to create a request object.
            request.parse(request_data)
            
            # Process the request and obtain the http response by
            # parsing the request and the predefined request processor.
            # This method also finalizes response by default.
            response = self.microapp._view(
                request,
                RequestProcessor(request),
            )
            
            # Validate the response type.
            response = to_response(response)
            
            # Send the http response back to client
            response_handler.send_response(
                response,
                client_socket=request.client_socket,
                request=request,
                disable_logging=self.microapp.no_logs,
            )

        except Exception as e:
            # Encountered an unknown error.
            from duck.http.core.wsgi import get_server_error_response
            
            # Send an http server error response to client.
            response = get_server_error_response(e, request)
           
            # Finalize server error response
            WSGI.finalize_response(response, request)
            
            response_handler.send_response(
                response,
                client_socket=request.client_socket,
                request=request,
                disable_logging=self.microapp.no_logs,
            )
            
            if not self.microapp.no_logs:
                # If logs are not disabled for the micro application, log error immediately
                logger.log_exception(e)
