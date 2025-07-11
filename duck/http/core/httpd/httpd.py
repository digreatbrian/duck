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

from functools import partial
from typing import (
    Optional,
    Tuple,
    Coroutine,
    Union,
    Callable,
)
from duck.contrib.responses import (
    simple_response,
    template_response,
)
from duck.contrib.sync import (
    iscoroutinefunction,
    sync_to_async,
)
from duck.http.core.handler import (
    ResponseHandler,
    log_response,
)
from duck.settings import SETTINGS
from duck.settings.loaded import (
    REQUEST_HANDLING_TASK_EXECUTOR,
    REQUEST_CLASS,
    ASGI, WSGI
)
from duck.exceptions.all import SettingsError
from duck.logging import logger
from duck.meta import Meta
from duck.http.core.processor import (
    AsyncRequestProcessor,
    RequestProcessor,
)
from duck.http.request import HttpRequest
from duck.http.request_data import (
    RawRequestData,
    RequestData,
)
from duck.http.response import (
    HttpRequestTimeoutResponse,
    HttpResponse,
)
from duck.contrib.responses.errors import get_timeout_error_response 
from duck.utils.dateutils import (
    django_short_local_date,
    short_local_date,
)
from duck.utils.ssl import is_ssl_data
from duck.utils.sockservers import xsocket
from duck.utils.lazy import Lazy


KEEP_ALIVE_PATTERN = re.compile(rb"(?i)\bConnection\s*:\s*keep\s*-?\s*alive\b")
KEEP_ALIVE_TIMEOUT = SETTINGS["KEEP_ALIVE_TIMEOUT"]
SERVER_POLL = SETTINGS["SERVER_POLL"]
SERVER_BUFFER = SETTINGS["SERVER_BUFFER"]
REQUEST_TIMEOUT = SETTINGS["REQUEST_TIMEOUT"]
STREAM_TIMEOUT = SETTINGS["REQUEST_STREAM_TIMEOUT"]
CONNECTION_MODE = SETTINGS["CONNECTION_MODE"]
CONTENT_LENGTH_PATTERN = re.compile(rb"(?i)content-length:\s*(\d+)")
TRANSFER_ENCODING_PATTERN = re.compile(rb"(?i)transfer-encoding:\s*([^\r\n]+)")
# Class for sending and logging resoponses
response_handler = Lazy(ResponseHandler)


def call_request_handling_executor(task: Union[threading.Thread, Coroutine]):
    """
    This calls the request handling executor with the provided task (thread or coroutine) and the 
    request handling executor keyword arguments set in settings.py.
    """
    REQUEST_HANDLING_TASK_EXECUTOR.execute(task) # execute thread or coroutine.


class BaseServer:
    """
    Base server class containing core server definitions and behaviors.
    
    Features:
    - HTTP Keep-Alive support for persistent connections.
    - Support for incoming requests using chunked Transfer-Encoding.
    - Synchronous + Asynchronous request handling using `WSGI` or `ASGI`.'
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
        Starts the `HTTP(S)` server.

        Args:
            no_logs (bool, optional): Whether to or not to log messages like `started server on ...` (defaults to False)
            domain (str, optional): Explicit domain that will be logged alongside the log messages.
        """
        host, port = self.addr
        
        if SETTINGS["DEBUG"]:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        
        self.sock.bind(self.addr)  # bind socket to (address, port)
        self.sock.listen(SETTINGS["REQUESTS_BACKLOG"]) # 200 by default
        
        # Prepare server setup
        duck_host = domain or Meta.get_metadata("DUCK_SERVER_HOST")
        duck_host = (list(duck_host)[0] if isinstance(duck_host, tuple) else duck_host or "localhost")
        server_url = "https" if self.enable_ssl else "http"
        server_url += f"://{duck_host}:{port}"
        server_gateway = "WSGI" if not SETTINGS['ASYNC_HANDLING'] else "ASGI"
        
        if not no_logs:
            if SETTINGS["DEBUG"]:
                logger.log(f"Started Duck {server_gateway} Server on {server_url}", level=logger.DEBUG)
            else:
                logger.log(
                    f"Started Duck Pro {server_gateway} Server on {server_url}\n  ├── PRODUCTION SERVER (domain: {domain or 'Not set'}) \n  "
                    f"└── This is a production server, stay secure!",
                     level=logger.DEBUG,
                 )
                 
                if SETTINGS['SUPPORT_HTTP_2'] or SETTINGS['ASYNC_HANDLING']:
                     if SETTINGS['ASYNC_LOOP'] != "uvloop":
                         logger.log(
                             "Default asyncio loop enabled, 'uvloop' is recommended for better performance.", 
                             level=logger.WARNING,
                         )
        
        # Listen and set the server in running state
        self.running = True
        
        # Listen and accept incoming connections
        while self.running:
            try:
                # Accept incoming connections
                sock = None
                
                if self.uses_ipv6:
                    sock = self.accept_and_handle_ipv6()
                else:
                    sock = self.accept_and_handle_ipv4()
                
            except ssl.SSLError as e:
                # Wrong protocol used e.g., https on http or vice versa
                if sock:
                    self.close_socket(sock)
                    
                if not no_logs and SETTINGS["VERBOSE_LOGGING"] and SETTINGS["DEBUG"]:
                    if "HTTP_REQUEST" in str(e):
                        logger.log(f"Client may be trying to connect with https on http server or vice-versa: {e}", level=logger.WARNING)
            
            except ConnectionResetError:
                pass
        
            except Exception as e:
                if sock:
                    self.close_socket(sock)
                    
                if not no_logs:
                    logger.log_exception(e)

    def stop_server(self, log_to_console: bool = True):
        """
        Stops the http(s) server.
        
        Args:
            log_to_console (bool): Log the message that the sever stoped. Defaults to True.
        """
        bold_start = "\033[1m"
        bold_end = "\033[0m"
        self.running = False
        self.close_socket(self.sock)
        
        if log_to_console: # log message indicating server stopped.
            logger.log_raw('\n')
            logger.log(
                f"{bold_start}Duck server stopped!{bold_end}",
                level=logger.INFO,
                custom_color=logger.Fore.MAGENTA,
            )
            
            # Redo socket close to ensure server stopped.
            self.running = False
            self.close_socket(self.sock)
    
    def accept_and_handle_ipv6(self):
        """
        Accepts and handle IPV6 connection.
        
        Returns:
            xsocket: The client socket.
        """
        sock, (host, port, flowinfo, scopeid)  = self.sock.accept()
        sock = xsocket.from_socket(sock)
        addr = (host, port)
        async_handling = SETTINGS['ASYNC_HANDLING']
        args = (self.handle_conn if not async_handling else self.async_handle_conn, sock, addr, flowinfo, scopeid)
        
        if async_handling:
            self._start_async_task(*args)
        else:
            self._start_thread(*args)
        
        # Finally return the client socket.
        return sock
            
    def accept_and_handle_ipv4(self):
        """
        Accepts and handle IPV4 connection.
        
        Returns:
            xsocket: Client socket object.
        """
        sock, addr = self.sock.accept()
        sock = xsocket.from_socket(sock)
        async_handling = SETTINGS['ASYNC_HANDLING']
        args = (self.handle_conn if not async_handling else self.async_handle_conn, sock, addr)
        
        if async_handling:
            self._start_async_task(*args)
        else:
            self._start_thread(*args)
        
        # Finally return the client socket
        return sock
        
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
            addr (Tuple[str, int]): Client ip address and port.
            flowinfo (Optional): Flow info if IPv6.
            scopeid (Optional): Scope id if IPv6.
        """
        sock.addr = addr
        sock.flowinfo = flowinfo
        sock.scopeid = scopeid
        
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
        
        # Close client socket just in case it is not closed
        self.close_socket(sock)
    
    async def async_handle_conn(
        self,
        sock: socket.socket,
        addr: Tuple[str, int],
        flowinfo: Optional = None,
        scopeid: Optional = None,
    ) -> None:
        """
        Main entry point to handle new connection asynchronously (supports both ipv6 and ipv4).

        Args:
            sock (socket.socket): The client socket object.
            addr (Tuple[str, int]): Client ip address and port.
            flowinfo (Optional): Flow info if IPv6.
            scopeid (Optional): Scope id if IPv6.
        """
        sock.addr = addr
        sock.flowinfo = flowinfo
        sock.scopeid = scopeid
        
        try:
            # Receive the full request (in bytes)
            data = await self.async_receive_full_request(sock, self.request_timeout)
        except TimeoutError:
            # For the first request, client took too long to respond.
            await self.async_do_request_timeout(sock, addr)
            return
        
        if not data:
            # Client sent an empty request, terminate the connection immediately
            await self.close_socket(sock)
            return
        
        # Process data/request 
        await self.async_process_data(sock, addr, RawRequestData(data))
        
        # Close client socket just in case it is not closed
        self.close_socket(sock)
    
    def process_data(self, sock, addr, request_data: RawRequestData):
        """
        Process and handle the request dynamically
        """
        data = request_data.data if isinstance(request_data, RawRequestData) else request_data.content
        
        if is_ssl_data(data):
            if SETTINGS['DEBUG']:
                logger.log(
                    "Data should be decoded at this point but it seems like it's ssl data",
                    level=logger.WARNING,
                )
                logger.log(f"Client may be trying to connect with https on http server or vice-versa\n", level=logger.WARNING)
            return None
            
        try:
            self.process_and_handle_request(sock, addr, request_data)
        except Exception as e:
            # processing and handling error resulted in an error
            # log the error message
            logger.log_exception(e)
        
        finally:
            keep_alive_re = KEEP_ALIVE_PATTERN
            
            # Check if client wants a keep alive connection
            # Only handle keep alive connection if the server supports it.
            if keep_alive_re.search(data.split(b"\r\n\r\n")[0]):  # target headers only
                if self.connection_mode == "keep-alive":
                    # server supports keep alive
                    self.handle_keep_alive_conn(sock, addr)
            
            # Finally close the socket if everything is finished
            self.close_socket(sock)
    
    async def async_process_data(self, sock, addr, request_data: RawRequestData):
        """
        Process and handle the request dynamically and asynchronously
        """
        data = request_data.data if isinstance(request_data, RawRequestData) else request_data.content
        
        if is_ssl_data(data):
            if SETTINGS['DEBUG']:
                logger.log(
                    "Data should be decoded at this point but it seems like it's ssl data",
                    level=logger.WARNING,
                )
                logger.log(f"Client may be trying to connect with https on http server or vice-versa\n", level=logger.WARNING)
            return None
            
        try:
            await self.async_process_and_handle_request(sock, addr, request_data)
        except Exception as e:
            # processing and handling error resulted in an error
            # log the error message
            logger.log_exception(e)
        
        finally:
            keep_alive_re = KEEP_ALIVE_PATTERN
            
            # Check if client wants a keep alive connection
            # Only handle keep alive connection if the server supports it.
            if keep_alive_re.search(data.split(b"\r\n\r\n")[0]):  # target headers only
                if self.connection_mode == "keep-alive":
                    # server supports keep alive
                    await self.async_handle_keep_alive_conn(sock, addr)
            
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
                data = self.receive_full_request(sock, KEEP_ALIVE_TIMEOUT)
                
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
                keep_alive_re = KEEP_ALIVE_PATTERN
                
                if keep_alive_re.search(data.split(b"\r\n\r\n")[0]):
                    # client seem to like to continue with keep alive connection
                    if self.connection_mode == "keep-alive":
                        # keep connection alive
                        continue
                    else:
                        break
                else:
                    # Client would like to terminate keep alive connection.
                    break
    
    async def async_handle_keep_alive_conn(
        self,
        sock: socket.socket,
        addr: Tuple[str, int],
    ) -> None:
        """
        Processes and handles keep alive connection asynchronously.
        """
        
        # Assume the client wants keep alive to run forever until explicitly stated to end it.
        while True:
            try:
                # Receive client request with a timeout.
                data = await self.async_receive_full_request(sock, KEEP_ALIVE_TIMEOUT)
                
                if not data:
                    # Client sent nothing or closed connection
                    # End the keep alive data exchange immediately
                    break
                
                # Process and handle the complete request using appropriate WSGI
                await self.async_process_and_handle_request(sock, addr, RawRequestData(data))
            
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
                keep_alive_re = KEEP_ALIVE_PATTERN
                
                if keep_alive_re.search(data.split(b"\r\n\r\n")[0]):
                    # client seem to like to continue with keep alive connection
                    if self.connection_mode == "keep-alive":
                        # keep connection alive
                        continue
                    else:
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
            disable_logging=no_logs,
         )
        
        # Close client socket immediately
        self.close_socket(sock)
    
    async def async_do_request_timeout(
        self,
        sock: socket.socket,
        addr: Tuple[str, int],
        no_logs: bool = False,
    ):
        """
        Sends request timeout response to client and close connection asynchronously.

        Args:
                sock (socket.socket): Client socket object
                addr (Tuple[str, int]): Client ip address and port.
                no_logs (bool): Whether to log response to console.
        """
        # Send timeout error message to client.
        timeout_response = get_timeout_error_response(timeout=self.request_timeout)
        
        # Send timeout response
        await response_handler.async_send_response(
            timeout_response,
            sock,
            disable_logging=no_logs,
         )
        
        # Close client socket immediately
        self.close_socket(sock)
        
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
                addr (Tuple[str, int]): Tuple for ip and port from where this request is coming from, ie Client addr
                request_data (RequestData): The request data object
        """
        handle_wsgi_request = WSGI
        
        handle_wsgi_request(
            self.application,
            sock,
            addr,
            request_data,
        )
    
    async def async_process_and_handle_request(
        self,
        sock: socket.socket,
        addr: Tuple[str, int],
        request_data: RequestData,
    ) -> None:
        """
        Asynchronously processes the request using WSGI application callable.

        Args:
                sock (socket.socket): Client Socket object
                addr (Tuple[str, int]): Tuple for ip and port from where this request is coming from, ie Client addr
                request_data (RequestData): The request data object
        """
        handle_asgi_request = ASGI
        
        await handle_asgi_request(
            self.application,
            sock,
            addr,
            request_data,
        )

    def receive_data(
        self,
        sock: socket.socket,
        timeout: Union[int, float] = REQUEST_TIMEOUT,
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
    
    async def async_receive_data(
        self,
        sock: socket.socket,
        timeout: Union[int, float] = REQUEST_TIMEOUT,
    ) -> bytes:
        """
        Asynchronously receives data from the socket but raises a TimeoutError if no data is received within the specified time.

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
            data = await sync_to_async(sock.recv, thread_sensitive=True)(self.buffer)
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
        timeout: Union[int, float] = REQUEST_TIMEOUT,
        stream_timeout: Union[int, float] = STREAM_TIMEOUT,
     ) -> bytes:
        """
        Receives the complete request data from the socket.
        
        Args:
                sock (socket.socket): The socket object
                timeout (Union[int, float]): Timeout in seconds to receive the first part of the data.
                stream_timeout (Union[int, float]):
                    The timeout in seconds to receive the next stream of
                    bytes after the first part has been received.
        
        Raises:
                TimeoutError: If no data is received within the first timeout (not stream timeout).

        Returns:
                bytes: The received data in bytes.
        """
        try:
            # Receive the first part of data
            data = self.receive_data(sock, timeout)
        
        except (ConnectionResetError, TimeoutError, Exception):
            # Return empty bytes
            return b""
        
        def receive_data_upto_headers_end(data: bytearray):
            """
            Receives data until all headers have been received.
            
            Raises:
                ConnectionResetError: On connection close.
                TimeoutError: If we receive nothing in certain timeframe.
                Exception: Any unknown exception.
            """
            # Receive data until there is enough \r\n\r\n
            while not b"\r\n\r\n" in data:
                data += self.receive_data(sock, timeout)
            
        
        def receive_data_using_content_length(data: bytearray, content_length: int):
            """
            Receive more data using the content-length header.
            """
            _, received_content = data.split(b"\r\n\r\n", 1)        
            received_length = len(received_content)
            
            while received_length < content_length:
                try:
                    # Receive data with a stream timeout
                    more_data = self.receive_data(sock, timeout)
                    data += more_data
                    received_length += len(more_data)
                    if not more_data:
                        # Data received is empty, this may mean the client is done sending.
                        break
                    
                except (ConnectionResetError, TimeoutError, Exception):
                    return
                    
        def receive_data_using_transfer_encoding(data: bytearray, encoding: bytes):
            """
            Efficiently receive and process data using the 'chunked' transfer-encoding.
            Only 'chunked' is supported.
        
            Args:
                data (bytearray): Mutable bytearray holding already received request data.
                encoding (bytes): Value of the Transfer-Encoding header.
        
            Raises:
                Exception: On invalid chunk sizes or unexpected stream errors.
            """
            if encoding.strip().lower() != b"chunked":
                receive_data_using_streaming_method(data)
                return
        
            _, body = data.split(b"\r\n\r\n", 1)
            body_offset = len(data) - len(body)
        
            while True:
                # Read chunk size line
                while b"\r\n" not in data[body_offset:]:
                    try:
                        more = self.receive_data(sock, stream_timeout)
                        data += more
                    except (ConnectionResetError, TimeoutError, Exception):
                        return
                        
                # Parse chunk size
                try:
                    newline_index = data.index(b"\r\n", body_offset)
                    chunk_size_line = data[body_offset:newline_index]
                    chunk_size = int(chunk_size_line.split(b";")[0].strip(), 16)
                except Exception:
                    return  # Invalid chunk size line
        
                body_offset = newline_index + 2  # Move past \r\n
        
                if chunk_size == 0:
                    # Final chunk
                    # Receive the trailing \r\n after the final chunk
                    while len(data) < body_offset + 2:
                        try:
                            more = self.receive_data(sock, stream_timeout)
                            data += more
                        except (ConnectionResetError, TimeoutError, Exception):
                            return
                    return
        
                # Receive chunk data + \r\n
                remaining = chunk_size + 2  # chunk data + trailing \r\n
                while len(data) - body_offset < remaining:
                    try:
                        more = self.receive_data(sock, stream_timeout)
                        data += more
                    except (ConnectionResetError, TimeoutError, Exception):
                        return
        
                body_offset += remaining  # Move offset past the full chunk
            
        def receive_data_using_streaming_method(data: bytearray):
            """
            Receive data through streaming interval method where if we 
            don't receive data within specific timeout, that means the data is complete.
            """
            while True:
                try:
                    # Receive data with a stream timeout
                    more_data = self.receive_data(sock, stream_timeout)
                    data += more_data
                    if not more_data:
                        # Data received is empty, this may mean the client is done sending.
                        break
                except (ConnectionResetError, TimeoutError, Exception):
                    return
        
        if data:
            # First part of data is not empty
            # Prefer receive_data_using_content_length over receive_data_using_streaming_method, these
            # approaches modify data inplace.
            
            # Modify data to be mutable in nested functions
            data = bytearray(data)
            
            try:
                # Receive until headers are complete.
                receive_data_upto_headers_end(data)
            except (ConnectionResetError, TimeoutError, Exception):
                return bytes(data)    
            
            encoding_match = TRANSFER_ENCODING_PATTERN.search(data)
            
            if encoding_match:
                receive_data_using_transfer_encoding(data, encoding_match.group(1))
                return bytes(data)
            
            # Try to extract Content-Length using a regex (fast, direct)
            length_match = CONTENT_LENGTH_PATTERN.search(data)
            
            if length_match:
                try:
                    content_length = int(length_match.group(1))
                    receive_data_using_content_length(data, content_length)
                except ValueError:               
                    receive_data_using_streaming_method(data)
            else:
                receive_data_using_streaming_method(data)
            
        # Return the received data
        return bytes(data)
        
    async def async_receive_full_request(
        self,
        sock: socket.socket,
        timeout: Union[int, float] = REQUEST_TIMEOUT,
        stream_timeout: Union[int, float] = STREAM_TIMEOUT,
     ) -> bytes:
        """
        Asynchronously receives the complete request data from the socket.
        
        Args:
                sock (socket.socket): The socket object
                timeout (Union[int, float]): Timeout in seconds to receive the first part of the data.
                stream_timeout (Union[int, float]):
                    The timeout in seconds to receive the next stream of
                    bytes after the first part has been received.
        
        Raises:
                TimeoutError: If no data is received within the first timeout (not stream timeout).

        Returns:
                bytes: The received data in bytes.
        """
        try:
            # Receive the first part of data
            data = await self.async_receive_data(sock, timeout)
        
        except (ConnectionResetError, TimeoutError, Exception):
            # Return empty bytes
            return b""
        
        async def receive_data_upto_headers_end(data: bytearray):
            """
            Receives data until all headers have been received.
            
            Raises:
                ConnectionResetError: On connection close.
                TimeoutError: If we receive nothing in certain timeframe.
                Exception: Any unknown exception.
            """
            # Receive data until there is enough \r\n\r\n
            while not b"\r\n\r\n" in data:
                data += await self.async_receive_data(sock, timeout)
            
        
        async def receive_data_using_content_length(data: bytearray, content_length: int):
            """
            Receive more data using the content-length header.
            """
            _, received_content = data.split(b"\r\n\r\n", 1)        
            received_length = len(received_content)
            
            while received_length < content_length:
                try:
                    # Receive data with a stream timeout
                    more_data = await self.async_receive_data(sock, timeout)
                    data += more_data
                    received_length += len(more_data)
                    if not more_data:
                        # Data received is empty, this may mean the client is done sending.
                        break
                    
                except (ConnectionResetError, TimeoutError, Exception):
                    return
                    
        async def receive_data_using_transfer_encoding(data: bytearray, encoding: bytes):
            """
            Efficiently receive and process data using the 'chunked' transfer-encoding.
            Only 'chunked' is supported.
        
            Args:
                data (bytearray): Mutable bytearray holding already received request data.
                encoding (bytes): Value of the Transfer-Encoding header.
        
            Raises:
                Exception: On invalid chunk sizes or unexpected stream errors.
            """
            if encoding.strip().lower() != b"chunked":
                await receive_data_using_streaming_method(data)
                return
        
            _, body = data.split(b"\r\n\r\n", 1)
            body_offset = len(data) - len(body)
        
            while True:
                # Read chunk size line
                while b"\r\n" not in data[body_offset:]:
                    try:
                        more = await self.async_receive_data(sock, stream_timeout)
                        data += more
                    except (ConnectionResetError, TimeoutError, Exception):
                        return
                        
                # Parse chunk size
                try:
                    newline_index = data.index(b"\r\n", body_offset)
                    chunk_size_line = data[body_offset:newline_index]
                    chunk_size = int(chunk_size_line.split(b";")[0].strip(), 16)
                except Exception:
                    return  # Invalid chunk size line
        
                body_offset = newline_index + 2  # Move past \r\n
        
                if chunk_size == 0:
                    # Final chunk
                    # Receive the trailing \r\n after the final chunk
                    while len(data) < body_offset + 2:
                        try:
                            more = await self.async_receive_data(sock, stream_timeout)
                            data += more
                        except (ConnectionResetError, TimeoutError, Exception):
                            return
                    return
        
                # Receive chunk data + \r\n
                remaining = chunk_size + 2  # chunk data + trailing \r\n
                while len(data) - body_offset < remaining:
                    try:
                        more = await self.async_receive_data(sock, stream_timeout)
                        data += more
                    except (ConnectionResetError, TimeoutError, Exception):
                        return
        
                body_offset += remaining  # Move offset past the full chunk
            
        async def receive_data_using_streaming_method(data: bytearray):
            """
            Receive data through streaming interval method where if we 
            don't receive data within specific timeout, that means the data is complete.
            """
            while True:
                try:
                    # Receive data with a stream timeout
                    more_data = await self.async_receive_data(sock, stream_timeout)
                    data += more_data
                    if not more_data:
                        # Data received is empty, this may mean the client is done sending.
                        break
                except (ConnectionResetError, TimeoutError, Exception):
                    return
        
        if data:
            # First part of data is not empty
            # Prefer receive_data_using_content_length over receive_data_using_streaming_method, these
            # approaches modify data inplace.
            
            # Modify data to be mutable in nested functions
            data = bytearray(data)
            
            try:
                # Receive until headers are complete.
                await receive_data_upto_headers_end(data)
            except (ConnectionResetError, TimeoutError, Exception):
                return bytes(data)    
            
            encoding_match = TRANSFER_ENCODING_PATTERN.search(data)
            
            if encoding_match:
                await receive_data_using_transfer_encoding(data, encoding_match.group(1))
                return bytes(data)
            
            # Try to extract Content-Length using a regex (fast, direct)
            length_match = CONTENT_LENGTH_PATTERN.search(data)
            
            if length_match:
                try:
                    content_length = int(length_match.group(1))
                    await receive_data_using_content_length(data, content_length)
                except ValueError:               
                    await receive_data_using_streaming_method(data)
            else:
                await receive_data_using_streaming_method(data)
            
        # Return the received data
        return bytes(data)
        
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
        sock.t0 = time.perf_counter()
        
        if flowinfo is not None and scopeid is not None:
            args.extend([flowinfo, scopeid])

        task = partial(target, *args)
        task.name=f"client-{ip}@{port}"
        
        # Execute request handling in new thread
        call_request_handling_executor(task)

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
        
        if iscoroutinefunction(target):
            # Execute request handling coroutine
            coro = target(*args)
            call_request_handling_executor(coro)
        
        else:
            # Execute request handling coroutine
            call_request_handling_executor(sync_to_async(target, thread_sensitive=True)(*args))


class BaseMicroServer:
    """
    BaseMicroServer class containing definitions for micro application server.
    
    This class is the base definition of a micro application server.
    """

    def set_microapp(self, microapp):
        """Sets the target micro application for this server instance."""
        from duck.app.microapp import MicroApp

        if not isinstance(microapp, MicroApp):
            raise ValueError(f"MicroApp instance expected, received {type(micropp)} instead.")
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
        
        request_class = REQUEST_CLASS

        if not issubclass(request_class, HttpRequest):
            raise SettingsError(
                f"REQUEST_CLASS set in settings.py should be an instance of Duck HttpRequest not {request_class}"
            )
        
        try:
            request = request_class(
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
        
    async def async_process_and_handle_request(
        self,
        sock: socket.socket,
        addr: Tuple[str, int],
        request_data: RequestData,
    ) -> None:
        """
        Processes and handles the request asynchronously.

        Args:
            sock (socket.socket): The target client socket.
            addr (Tuple): The client address and port.
            request_data (RequestData): The full request data object.
        """
        from duck.shortcuts import to_response
        from duck.settings.loaded import ASGI, REQUEST_CLASS 

        request_class = REQUEST_CLASS

        if not issubclass(request_class, HttpRequest):
            raise SettingsError(
                f"REQUEST_CLASS set in settings.py should be an instance of Duck HttpRequest not {request_class}"
            )
        
        try:
            request = request_class(
                client_socket=sock,
                client_address=addr,
            ) # create an http request instance.
            
            # Parse request data to create a request object.
            await sync_to_async(request.parse, thread_sensitive=False)(request_data)
            
            # Process the request and obtain the http response by
            # parsing the request and the predefined request processor.
            # This method also finalizes response by default.
            response = await self.microapp._async_view(
                request,
                AsyncRequestProcessor(request),
            )
            
            # Validate the response type.
            response = to_response(response)
            
            # Send the http response back to client
            await response_handler.async_send_response(
                response,
                client_socket=request.client_socket,
                request=request,
                disable_logging=self.microapp.no_logs,
            )

        except Exception as e:
            # Encountered an unknown error.
            from duck.http.core.asgi import get_server_error_response
            
            # Send an http server error response to client.
            response = get_server_error_response(e, request)
           
            # Finalize server error response
            await ASGI.finalize_response(response, request)
            
            await response_handler.async_send_response(
                response,
                client_socket=request.client_socket,
                request=request,
                disable_logging=self.microapp.no_logs,
            )
            
            if not self.microapp.no_logs:
                # If logs are not disabled for the micro application, log error immediately
                logger.log_exception(e)
