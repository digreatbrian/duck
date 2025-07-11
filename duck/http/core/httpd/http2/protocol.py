"""
H2 Protocol responsible for handling H2 Connections.
"""
import ssl
import time
import select
import queue
import socket
import asyncio

from functools import partial
from typing import (
    Tuple,
    Union,
    Optional,
    Callable,
)
from asgiref.sync import sync_to_async

from h2.config import H2Configuration
from h2.connection import H2Connection, ConnectionState
from h2.exceptions import ProtocolError, StreamClosedError

from duck.settings import SETTINGS
from duck.http.request import HttpRequest
from duck.http.response import (
    BaseResponse,
    HttpResponse,
    StreamingHttpResponse,
)
from duck.http.core.handler import ResponseHandler
from duck.http.core.httpd.http2 import BaseServer
from duck.http.core.httpd.http2.event_handler import EventHandler
from duck.logging import logger


class H2Protocol:
    """
    Asynchronous H2 Protocol class.
    """
    __slots__ = (
        "sock",
        "addr",
        "conn",
        "server",
        "event_handler",
        "event_loop",
        "sync_queue",
        "_closing"
    )
    
    def __init__(
        self,
        sock: socket.socket,
        addr: Tuple[str, int],
        conn: H2Connection,
        server: BaseServer,
        event_handler: EventHandler,
        event_loop: asyncio.BaseEventLoop = None,
        sync_queue: Optional[queue.Queue] = None,
    ):
        """
        H2Protocol initialization.
        
        Args:
            sock (socket.socket): Client socket object.
            addr (Tuple[str, int]): Client address.
            conn (H2Connection): H2 Connection object.
            server (BaseServer): The main server object.
            event_handler (EventHandler): Asynchrous `H2` event handler class.
            event_loop (asyncio.BaseEventLoop): The target event loop, only used in `WSGI` mode..
            sync_queue (Optional[queue.Queue]): A queue for adding tasks that needs to be executed outside async context,
                useful when threads are used and `ASYNC_HANDLING=False`
        """
        self.sock = sock
        self.addr = addr
        self.conn = conn
        self.server = server
        self.event_handler = event_handler
        self.event_loop = event_loop
        self.sync_queue = sync_queue
        self._closing = False
        
    async def run_forever(self):
        """
        Runs the loop for handling further client requests.
        """
        self.sock.setblocking(False)
        await self.async_send_pending_data()
        
        async def async_read_and_handle_data():
            """
            Receive and handle data asynchrously.
            """
            try:
                data = await self.server.async_receive_data(self.sock)
                if data:
                    await self.event_handler.entry(data)
                else:
                    self._closing = True
                    await self.async_send_goaway(0)
            
            except ProtocolError as e:
                logger.log(f"Protocol Error: {e}", level=logger.WARNING)
                logger.log_exception(e)
            
            except ssl.SSLError:
                pass
            
            except TimeoutError:
                pass
                
            except Exception as e:
                logger.log(f"HTTP/2 Error: {e}", level=logger.WARNING)
                logger.log_exception(e)
                
        # Read and handle H2 frames.
        while not  self._closing:
            await async_read_and_handle_data()
    
    def connection_lost(self, *_):
        """
        Called on socket connection lost.
        """
        self._closing = True
        
    def close_connection(self, error_code: int = 0, debug_message: bytes = None):
        """
        Closes the socket connection.
        """
        self._closing = True
        self.server.close_socket(self.sock)
        
    def send_data_to_sock(self, data: bytes):
        """
        Send data over the connected socket.
        """
        while True:
            _, wlist, _ = select.select([self.sock], [self.sock], [], 0)
            if wlist:
                try:
                    self.sock.sendall(data)
                except (ConnectionResetError, ssl.SSLError, OSError):
                    pass
                break
                    
    async def async_send_data_to_sock(self, data: bytes):
        """
        Send data over the connected socket asynchronously.
        """
        try:
             await sync_to_async(self.sock.sendall, thread_sensitive=True)(data)
        except (ConnectionResetError, ssl.SSLError, OSError):
             pass
                            
    def send_pending_data(self):
        """
        Sends any pending data from `H2Connection.data_to_send()`.
        """
        pending = self.conn.data_to_send()
        
        if pending:
            self.send_data_to_sock(pending)
    
    async def async_send_pending_data(self):
        """
        Asynchronously sends any pending data from `H2Connection.data_to_send()` asynchronously.
        """
        pending = self.conn.data_to_send()
        
        if pending:
            await self.async_send_data_to_sock(pending)
    
    def send_response(
        self,
        response: Union[BaseResponse, HttpResponse],
        stream_id: int,
        request: Optional[HttpRequest] = None,
        disable_logging: bool = False,
        suppress_errors: bool = False,
    ) -> None:
        """
        Synchronously sends an HTTP/2 response to the H2Connection.
        
        Args:
            response (Union[BaseResponse, HttpResponse]): The HTTP response object containing the response data.
            stream_id (int): The target H2 stream ID.
            request (Optional[HttpRequest]): The request object associated with the response. Used for logging and debugging purposes.
            disable_logging (bool): If True, disables logging of the response. Defaults to False.
            suppress_errors (bool): If True, suppresses any errors that occur during the sending process (only sending data). Defaults to False.

        Raises:
            Exception: If there is an error during the data sending process (e.g., socket errors), unless suppressed.
        
        This method calls `send_data` to transmit the raw response data to the client and 
        performs logging if `disable_logging` is False. If the request object contains 
        debug information or failed middleware details, they are included in the logs.
        """
        def log_response(response, request: Optional[HttpResponse], *_):
            """
            Logs the response to console after successful sending.
            """
            if not disable_logging:
                # Log response (if applicable)
                ResponseHandler.auto_log_response(response, request)
            
        def on_chunk_sent(chunk):
            """
            This increments the response fake content length size (useful for logging) everytime the chunk is sent.
            
            ``` {note}
            - This is very useful for tracking how much of response data have been delivered to the client.
            ```
            """
            content_size = response.content_obj.size or 0
            
            # Set response content fake size for logging purposes
            response.content_obj.set_fake_size(content_size + len(chunk))
        
        if self.conn.state_machine.state == ConnectionState.CLOSED:
            return
                
        real_content_length = response.get_header("content-length")
        
        if real_content_length:
            real_content_length = len(real_content_length)
            
            # Increment flow control window
            max_incr = 2147483647
            incr = min(real_content_length, max_incr)
            
            if real_content_length > 0 and real_content_length > 635535:
                self.conn.increment_flow_control_window(incr, stream_id)
        
        # Send any pending h2 data
        self.send_pending_data()
        
        try:
            headers = [(k.lower(), v) for k, v in response.headers.items()]
            
            for _, morsel in response.cookies.items():
                headers.append(("set-cookie", morsel.output(header="").strip()))
            
            headers.insert(0, (":status", str(response.status_code)))
            self.conn.send_headers(stream_id, headers)
             
            if not isinstance(response, StreamingHttpResponse):
                # Send response directly to client socket
                self.send_data(
                    response.content,
                    stream_id,
                    end_stream=False,
                    on_data_sent=on_chunk_sent,
                )
                
                # End or close stream
                self.send_data(
                    b"",
                    stream_id,
                    end_stream=True,
                    on_data_sent=partial(log_response, response, request),
                )
            
                # Send any pending data
                self.send_pending_data() 
                
            else:
                # Send response in chunks
                
                for chunk in response.iter_content():
                    if isinstance(chunk, str):
                        chunk = chunk.encode("utf-8")
                    
                    # Send chunk to client socket.
                    self.send_data(
                        chunk,
                        stream_id,
                        end_stream=False,
                        on_data_sent=on_chunk_sent,
                    )
                
                # End or close stream
                self.send_data(
                    b"",
                    stream_id,
                    end_stream=True,
                    on_data_sent=partial(log_response, response, request),
                )
            
                # Send any pending data
                self.send_pending_data()
                
        except Exception as e:
            if not suppress_errors:
                raise e
                
    async def async_send_response(
        self,
        response: Union[BaseResponse, HttpResponse],
        stream_id: int,
        request: Optional[HttpRequest] = None,
        disable_logging: bool = False,
        suppress_errors: bool = False,
    ) -> None:
        """
        Asynchronously sends an HTTP/2 response to the H2Connection.
        
        Args:
            response (Union[BaseResponse, HttpResponse]): The HTTP response object containing the response data.
            stream_id (int): The target H2 stream ID.
            request (Optional[HttpRequest]): The request object associated with the response. Used for logging and debugging purposes.
            disable_logging (bool): If True, disables logging of the response. Defaults to False.
            suppress_errors (bool): If True, suppresses any errors that occur during the sending process (only sending data). Defaults to False.

        Raises:
            Exception: If there is an error during the data sending process (e.g., socket errors), unless suppressed.
        
        This method calls `async_send_data` to transmit the raw response data to the client and 
        performs logging if `disable_logging` is False. If the request object contains 
        debug information or failed middleware details, they are included in the logs.
        """
        def log_response(response, request: Optional[HttpResponse], *_):
            """
            Logs the response to console after successful sending.
            """
            if not disable_logging:
                # Log response (if applicable)
                ResponseHandler.auto_log_response(response, request)
            
        def on_chunk_sent(chunk):
            """
            This increments the response fake content length size (useful for logging) everytime the chunk is sent.
            
            ``` {note}
            - This is very useful for tracking how much of response data have been delivered to the client.
            ```
            """
            content_size = response.content_obj.size or 0
            
            # Set response content fake size for logging purposes
            response.content_obj.set_fake_size(content_size + len(chunk))
        
        if self.conn.state_machine.state == ConnectionState.CLOSED:
            return
                
        real_content_length = response.get_header("content-length")
        
        if real_content_length:
            real_content_length = len(real_content_length)
            
            # Increment flow control window
            max_incr = 2147483647
            incr = min(real_content_length, max_incr)
            
            if real_content_length > 0 and real_content_length > 635535:
                self.conn.increment_flow_control_window(incr, stream_id)
        
        # Send any pending h2 data
        await self.async_send_pending_data()
        
        try:
            headers = [(k.lower(), v) for k, v in response.headers.items()]
            
            for _, morsel in response.cookies.items():
                headers.append(("set-cookie", morsel.output(header="").strip()))
            
            headers.insert(0, (":status", str(response.status_code)))
            self.conn.send_headers(stream_id, headers)
             
            if not isinstance(response, StreamingHttpResponse):
                # Send response directly to client socket
                await self.async_send_data(
                    response.content,
                    stream_id,
                    end_stream=False,
                    on_data_sent=on_chunk_sent,
                )
                
                # End or close stream
                await self.async_send_data(
                    b"",
                    stream_id,
                    end_stream=True,
                    on_data_sent=partial(log_response, response, request),
                )
            
                # Send any pending data
                await self.async_send_pending_data() 
                
            else:
                # Send response in chunks
                
                for chunk in response.iter_content():
                    if isinstance(chunk, str):
                        chunk = chunk.encode("utf-8")
                    
                    # Send chunk to client socket.
                    await self.async_send_data(
                        chunk,
                        stream_id,
                        end_stream=False,
                        on_data_sent=on_chunk_sent,
                    )
                
                # End or close stream
                await self.async_send_data(
                    b"",
                    stream_id,
                    end_stream=True,
                    on_data_sent=partial(log_response, response, request),
                )
            
                # Send any pending data
                await self.async_send_pending_data()
                
        except Exception as e:
            if not suppress_errors:
                raise e
        
    async def async_send_goaway(self, error_code, debug_message: bytes = None):
        """
        Sends a `GOAWAY` frame with the given error code and debug_message.
        """
        if self.conn.state_machine.state == ConnectionState.CLOSED:
            self.close_connection()
            return
        
        try:
            self.conn.close_connection(
                error_code,
                additional_data=debug_message or b""
            )
            await self.async_send_pending_data()
        except (BrokenPipeError, ConnectionResetError):
            pass
        
        except Exception as e:
            if "EOF occurred in violation of protocol" not in str(e) and "bad length" not in str(e):
                logger.log_raw(f"Error sending GOAWAY: {e}", level=logger.WARNING)
        
        finally:
            self.close_connection()
        
    def send_data(
        self,
        data: bytes,
        stream_id: int,
        end_stream: bool = False,
        on_data_sent: Callable = None,
    ):
        """
        Sends data synchronously according to flow control.
        
        Args:
            data (bytes): Data to send.
            stream_id (int): The respective stream ID for the data.
            end_stream (bool): Whether to close stream after sending the data. Defaults to False.
            on_data_sent (Optional[None]): Callable to execute right after all data has been sent. Defaults to None.
        
        Notes:
        - The first argument to `on_data_sent` callable is the data sent.
        """
        original_data = data # keep a reference to original data as `data` variable may be modified by while loop.
        self.send_pending_data() # send pending data before sending the real data
        
        while data:
            try:
                while self.conn.local_flow_control_window(stream_id) < 1:
                    try:
                        self.event_handler.sync_wait_for_flow_control(stream_id)
                    except asyncio.CancelledError:
                        return
            except StreamClosedError:
                break
                
            try:
                chunk_size = min(
                    self.conn.local_flow_control_window(stream_id),
                    len(data),
                    self.conn.max_outbound_frame_size,
                )
                
                self.flush_response_data(
                    data=data[:chunk_size],
                    stream_id=stream_id,
                    end_stream=end_stream,
                )
                
                data = data[chunk_size:] # move to the next chunk
                
            except (StreamClosedError, ProtocolError):
                break
            
        else:
            if not original_data and end_stream:
                # No data has been set yet end_stream is True, meaning we want to close the stream
                try:
                    self.conn.end_stream(stream_id)
                except (StreamClosedError, KeyError):
                    pass
                
                self.send_pending_data()
        
        if on_data_sent is not None:
            # Data has been successfully sent
            on_data_sent(original_data) # execute an event on data sent
            
    async def async_send_data(
        self,
        data: bytes,
        stream_id: int,
        end_stream: bool = False,
        on_data_sent: Callable = None,
    ):
        """
        Asynchronously Send data according to flow control.
        
        Args:
            data (bytes): Data to send.
            stream_id (int): The respective stream ID for the data.
            end_stream (bool): Whether to close stream after sending the data. Defaults to False.
            on_data_sent (Optional[None]): Callable to execute right after all data has been sent. Defaults to None.
        
        Notes:
        - The first argument to `on_data_sent` callable is the data sent.
        """
        original_data = data # keep a reference to original data as `data` variable may be modified by while loop.
        await self.async_send_pending_data() # send pending data before sending the real data
        
        while data:
            try:
                while self.conn.local_flow_control_window(stream_id) < 1:
                    try:
                        await self.event_handler.wait_for_flow_control(stream_id)
                    except asyncio.CancelledError:
                        return
            except StreamClosedError:
                break
                
            try:
                chunk_size = min(
                    self.conn.local_flow_control_window(stream_id),
                    len(data),
                    self.conn.max_outbound_frame_size,
                )
                
                await self.async_flush_response_data(
                    data=data[:chunk_size],
                    stream_id=stream_id,
                    end_stream=end_stream,
                )
                
                data = data[chunk_size:] # move to the next chunk
                
            except (StreamClosedError, ProtocolError):
                break
            
        else:
            if not original_data and end_stream:
                # No data has been set yet end_stream is True, meaning we want to close the stream
                try:
                    self.conn.end_stream(stream_id)
                except (StreamClosedError, KeyError):
                    pass
                
                await self.async_send_pending_data()
        
        if on_data_sent is not None:
            # Data has been successfully sent
            on_data_sent(original_data) # execute an event on data sent
            
    def flush_response_data(
        self,
        data: bytes,
        stream_id: int,
        end_stream: bool = False,
    ):
        """
        Sends response data directly to client socket.
        
        Notes:
        - This first response data to queue by sending it to `H2Connection` then fetch the
           response data from `H2Connection.data_to_send()` then sends the data.
        """
        self.conn.send_data(
            stream_id,
            data=data,
            end_stream=end_stream,
         )
        
        # Send pending data added to H2Connection.
        self.send_pending_data()
    
    async def async_flush_response_data(
        self,
        data: bytes,
        stream_id: int,
        end_stream: bool = False,
    ):
        """
        Asynchronously sends response data directly to client socket.
        
        Notes:
        - This first response data to queue by sending it to `H2Connection` then fetch the
           response data from `H2Connection.data_to_send()` then sends the data.
        """
        self.conn.send_data(
            stream_id,
            data=data,
            end_stream=end_stream,
         )
        
        # Send pending data added to H2Connection.
        await self.async_send_pending_data()
