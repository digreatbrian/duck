"""
Base server implementation for HTTP/2
"""
import re
import os
import h2
import ssl
import time
import socket
import asyncio

from typing import (
    Tuple,
    Dict,
    Optional,
    List,
    Callable,
)

from h2.config import H2Configuration
from h2.connection import H2Connection

from duck.settings import SETTINGS
from duck.http.response import (
    HttpResponse,
    HttpSwitchProtocolResponse,
)
from duck.http.request_data import RawRequestData
from duck.http.core.httpd.httpd import (
    BaseServer,
    response_handler,
)
from duck.utils.sockservers import xsocket
from duck.logging import logger
from duck.eventloop import AsyncioLoopManager


asyncio_loop_manager = None


if not SETTINGS["ASYNC_HANDLING"] and SETTINGS["SUPPORT_HTTP_2"]:
    asyncio_loop_manager = AsyncioLoopManager()
    asyncio_loop_manager.start()


# Set some django settings
if SETTINGS["SUPPORT_HTTP_2"] and not SETTINGS["ASYNC_HANDLING"]:
    # We are using threads, and we're using async only because HTTP/2 handling is async by nature (e.g., via h2).
    # But we're not running on a single-threaded event loop — so blocking isn’t dangerous for us.
    # This avoids Django’s SynchronousOnlyOperation error as it gets in the way even though we're safe.
    os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


class BaseHttp2Server(BaseServer):
    """
    Base server with addition of HTTP/2 protocol.
    """
    def set_h2_settings(self, h2_conn):
        """
        Sets the H2 settings on the unitiated h2 connection.
        """
        h2_conn.update_settings({
            h2.settings.SettingCodes.INITIAL_WINDOW_SIZE: 2**24,  # e.g., 16MB window
            h2.settings.SettingCodes.MAX_CONCURRENT_STREAMS: 100
        })
        
    def failsafe_process_and_handle_request(self, sock, addr, request_data):
        """
        Processes and handles a request but logs any encountered error.
        """
        def inner(sock, addr, request_data):
            try:
                self.process_and_handle_request(sock, addr, request_data)
            except Exception as e:
                # processing and handling error resulted in an error
                # log the error message
                logger.log_exception(e)
        inner(sock, addr, request_data)
        
    def handle_conn(
        self,
        sock: socket.socket,
        addr: Tuple[str, int],
        flowinfo: Optional = None,
        scopeid: Optional = None,
        strictly_http2: bool = True,
    ) -> None:
        """
        Main entry point to handle new connection (supports both ipv6 and ipv4).

        Args:
            sock (socket.socket): The client socket object.
            addr (Tuple[str, int]): Client ip and port.
            flowinfo (Optional): Flow info if IPv6.
            scopeid (Optional): Scope id if IPv6.
            strictly_http2 (bool): Whether to srtrictly use `HTTP/2` without checking if user selected it.
        """
        sock = xsocket.from_socket(sock)
        has_h2_alpn = hasattr(sock, 'selected_alpn_protocol') and sock.selected_alpn_protocol() == 'h2'
        
        if not has_h2_alpn or not strictly_http2:
            # Fallback to HTTP/1
            # The user selected alpn protocol is not h2, switch to default HTTP/1 only if Upgrade to h2c is not set
             
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
            
             # Regex to match "Upgrade: h2" or "Upgrade: h2c" in headers only
             upgrade_h2_regex = re.compile(
                 rb'^(?:[^\r\n]*\r\n)*Upgrade:\s*h2c?\s*(?:\r\n[^\r\n]*)*\r\n\r\n',
                 re.IGNORECASE | re.MULTILINE
              )
              
             # Regex to extract HTTP2-Settings header value
             settings_h2_pattern = re.compile(
                 rb"HTTP2-Settings:\s*([A-Za-z0-9+\/=]+)",
                 re.IGNORECASE | re.MULTILINE,
             )
             
             if upgrade_h2_regex.match(data):
                # Lets upgrade to HTTP/2
                settings_header = None
                settings_match = settings_h2_pattern.search(data)
                
                if settings_match:
                    settings_header = settings_match.group(1)
                
                config = H2Configuration(client_side=False)
                h2_connection = H2Connection(config=config)
                self.set_h2_settings(h2_connection)
                
                if settings_header:
                    h2_connection.initiate_upgrade_connection(settings_header=settings_header)
                else:
                    h2_connection.initiate_connection()
                
                # Send switching protocols response
                switching_proto_response = HttpSwitchProtocolResponse(upgrade_to="h2c")
                
                response_handler.send_response(
                    switching_proto_response,
                    client_socket=sock,
                    request=None,
                    strictly_http1=True,
                 )
                
                # Send pending Preamble HTTP/2 data.
                try:
                    response_handler.send_data(
                        h2_connection.data_to_send(),
                        client_socket=sock,
                        suppress_errors=False,
                    )
                except (BrokenPipeError, ConnectionResetError):
                    # Client disconnected 
                    return
                 
                # Handle the current request
                # Now parse full request for handling
                request_data = RawRequestData(data)
                request_data.request_store["stream_id"] = 1
                request_data.request_store["h2_handling"] = True
                
                # Handle connection as HTTP/2 compatible connection
                # Process and handle the initial request
                self.failsafe_process_and_handle_request(sock, self.addr, request_data)
                self.start_http2_loop(sock, addr, h2_connection)
             else:
                # No HTTP/2 Upgrade, strictly HTTP/1.1
                request_data = RawRequestData(data)
                request_data.request_store["h2_handling"] = False
                self.process_data(sock, self.addr, request_data)
             return 
        
        # Initiate and Send HTTP/2 Preamble
        config = H2Configuration(client_side=False)
        h2_connection = H2Connection(config=config)
        
        # Set H2 settings and initiate connection
        self.set_h2_settings(h2_connection)
        h2_connection.initiate_connection()
        
        # Send pending Preamble HTTP/2 data.
        try:
            response_handler.send_data(
                h2_connection.data_to_send(),
                client_socket=sock,
                suppress_errors=False,
            )
        except (BrokenPipeError, ConnectionResetError):
            # Client disconnected 
            return
        
        # Start HTTP/2 loop
        self.start_http2_loop(sock, addr, h2_connection)
    
    def start_http2_loop(self, sock, addr, h2_connection: H2Connection):
        """
        This starts the loop for handling HTTP/2 connection.
        """
        from duck.http.core.httpd.http2.protocol import H2Protocol
        from duck.http.core.httpd.http2.event_handler import EventHandler
        
        # Assume client supports HTTP/2
        event_loop = asyncio_loop_manager.loop or asyncio.get_event_loop()
        
        protocol = H2Protocol(
            sock=sock,
            addr=addr,
            conn=h2_connection,
            server=self,
            event_handler=None,
            event_loop=event_loop,
        )
        
        protocol.send_pending_data()
        protocol.event_handler = EventHandler(protocol=protocol)
        sock.h2_protocol = protocol
        coro = protocol.run_forever()
        
        if asyncio_loop_manager:
            asyncio_loop_manager.submit_task(coro)
        else:
            # Running in asyncio mode / no threads
            return asyncio.run_coroutine_threadsafe(coro, event_loop)
