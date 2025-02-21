"""
Base server implementation for HTTP/2
"""
import re
import ssl
import socket
import asyncio
import threading

from typing import Tuple, Dict, Optional, List, Callable

from h2.config import H2Configuration
from h2.connection import (
    H2Connection,
    ConnectionState,
)
from h2.events import (
    ConnectionTerminated,
    DataReceived,
    RemoteSettingsChanged,
    RequestReceived,
    StreamEnded,
    StreamReset,
    WindowUpdated
)
from h2.exceptions import (
    ProtocolError,
    StreamClosedError,
)
from h2.errors import ErrorCodes
from h2.settings import SettingCodes

from duck.settings import SETTINGS
from duck.http.core.httpd.httpd import (
    SERVER_BUFFER,
    BaseServer,
    response_handler,
)
from duck.http.response import HttpSwitchProtocolResponse
from duck.http.request_data import RequestData, RawRequestData
from duck.http.core.handler import ResponseHandler
from duck.utils.caching import InMemoryCache
from duck.utils.sockservers import xsocket
from duck.logging import logger


class EventHandler:
    """
    HTTP/2 Event handler.
    """
    
    streams = InMemoryCache()
    """
    In memory cache for all streams
    """
    def __init__(self, sock, addr, base_server):
        self.sock = sock
        self.addr = addr
        self.base_server = base_server
    
    def on_request_complete(self, event):
        """
        Event when we receive the full request (request is complete).
        """
        assert hasattr(self.sock, "h2_connection") and isinstance(self.sock.h2_connection, H2Connection), "Attribute sock.h2_connection must be set representing the H2Connection"
        
        # Get stream ID
        stream_id: int = event.stream_id
       
        # Try get the request data from streams
        request_data = self.streams.get(stream_id, pop=True)
        
        if not request_data:
           # The stream/body received has no headers, discard it
           # Just return, h2 probably 405'd this already
           return
        
        # Convert headers to dictionary according to HTTP/1 from HTTP/2
        # Set new headers for the request_data
        headers = request_data.headers
        
        topheader = "{method} {path} {http_version}".format(
             method=headers.pop(':method'),
             path=headers.pop(':path'),
             http_version='HTTP/2')
        
        if ":authority" in headers:
            authority = headers.pop(':authority')
            headers["host"] = authority
            
        request_data.headers["topheader"] = topheader
        
        # Set stream request data stream_id
        request_data.stream_id = stream_id
        
        # Now parse full request for handling
        try:
            self.base_server.process_and_handle_request(self.sock, self.addr, request_data)
        except Exception as e:
            # processing and handling error resulted in an error
            # log the error message
            logger.log_exception(e)
    
    def on_new_request(self, event):
       """
       Event called when we receive new request headers
       """
       # Get stream ID and headers
       stream_id: int = event.stream_id
       headers: List[Tuple[str, str]] = event.headers
       headers: Dict[str, str] = {header.decode('utf-8'): value.decode('utf-8') for (header, value) in headers}
        
       # Set initial request data for the stream
       request_data = RequestData(headers)
       self.streams.set(stream_id, request_data)
    
    def on_data_received(self, event):
        """
        We've received some data on a stream. If that stream is one we're
        expecting data on, save it off. Otherwise, reset the stream.
        """
        stream_id = event.stream_id
        request_data = self.streams.get(stream_id)
        
        if not request_data:
            self.sock.h2_connection.reset_stream(
                stream_id, error_code=ErrorCodes.PROTOCOL_ERROR
            )
        else:
            new_data = event.data
            request_data.content += new_data
        
        if event.stream_ended:
            self.on_request_complete(event)
        
    def on_stream_reset(self, event):
        """
        Event called on stream reset.
        """
        self.sock.h2_cancel_streams.add(event.stream_id)
        
    def on_connection_terminated(self, event):
        """
        Event called on connection termination.
        """
        self.sock.h2_keep_connection = False
        
    def dispatch_events(self, events: List):
        """
        Dispatch or handle events
        """
        
        for event in events:
            if isinstance(event, RequestReceived):
                self.on_new_request(event)
            
            elif isinstance(event, DataReceived):
                 self.on_data_received(event)
                 
                 # Acknowledge that we've processed the data to update the flow control window
                 self.sock.h2_connection.acknowledge_received_data(event.flow_controlled_length, event.stream_id)
                 
            elif isinstance(event, WindowUpdated):
                  # Update flow control window if necessary
                  self.sock.h2_connection.increment_flow_control_window(event.delta)
                 
            elif isinstance(event, StreamReset):
                 self.on_stream_reset(event)
            
            elif isinstance(event, ConnectionTerminated):
                 self.on_connection_terminated(event)
            
            elif isinstance(event, StreamEnded):
                 # Set the current event
                 self.on_request_complete(event)
        

class BaseHttp2Server(BaseServer):
    """
    Base server with addition of HTTP/2 protocol.
    """
    def handle_conn(
        self,
        sock: socket.socket,
        addr: Tuple[str, int],
        flowinfo: Optional = None,
        scopeid: Optional = None,
        strictly_http2: bool = False,
    ) -> None:
        """
        Main entry point to handle new connection (supports both ipv6 and ipv4).

        Args:
            sock (socket.socket): The client socket object.
            addr (Tuple[str, int]): Client ip and port.
            flowinfo (Optional): Flow info if IPv6.
            scopeid (Optional): Scope id if IPv6.
            strictly_http2 (bool): Whether to srtrictly use http2 without checking if user selected it
        """
        sock = xsocket.from_socket(sock)
        
        if not ((hasattr(sock, 'selected_alpn_protocol')
            and sock.selected_alpn_protocol() == 'h2') or  strictly_http2):
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
                
                if settings_header:
                    h2_connection.initiate_upgrade_connection(settings_header=settings_header)
                else:
                    h2_connection.initiate_connection()
                
                # Send switching protocols response
                switching_proto_response = HttpSwitchProtocolResponse(upgrade_to="h2c")
                response_handler.send_response(
                    switching_proto_response,
                    client_socket=sock,
                    request=None)
                
                # Send pending HTTP/2 data.
                try:
                    response_handler.send_data(
                        h2_connection.data_to_send(),
                        sock, suppress_errors=False)
                except (BrokenPipeError, ConnectionResetError):
                    # Client disconnected 
                    return
                    
                # Set attributes and Handle the current request
                sock.h2_handling = True
                sock.h2_connection = h2_connection
                sock.h2_cancel_streams = set()
                sock.h2_keep_connection = True
                sock.h2_event_handler = EventHandler(sock=sock, addr=addr, base_server=self)
                
                # Handle the current request
                # Now parse full request for handling
                request_data = RawRequestData(data)
                request_data.stream_id = 1
                
                try:
                    self.process_and_handle_request(sock, self.addr, request_data)
                except Exception as e:
                    # processing and handling error resulted in an error
                    # log the error message
                    logger.log_exception(e)
                
                # Handle connection as HTTP/2 compatible connection
                self.start_http2_loop(sock, addr, h2_connection)
             else:
                self.process_data(sock, addr, data)
             return 
        
        # Initiate and Send HTTP/2 Preamble
        config = H2Configuration(client_side=False)
        h2_connection = H2Connection(config=config)
        h2_connection.initiate_connection()
        
        # Send Preamble
        response_handler.send_data(
            h2_connection.data_to_send(),
            sock, suppress_errors=False)
    
        # Start HTTP/2 loop
        self.start_http2_loop(sock, addr, h2_connection)
    
    def start_http2_loop(self, sock, addr, h2_connection: H2Connection):
        """
        This starts the loop for handling HTTP/2 connection.
        """
        # Assume client support HTTP/2
        self._start_http2_loop(sock, addr, h2_connection)   
     
    def _start_http2_loop(self, sock, addr, h2_connection: H2Connection):
        """
        This starts the loop for handling HTTP/2 connection.
        """
        # Assume client support HTTP/2
        sock.h2_handling = True
        sock.h2_connection = h2_connection
        sock.h2_cancel_streams = set()
        sock.h2_keep_connection = True
        sock.h2_event_handler = EventHandler(sock=sock, addr=addr, base_server=self)
        
        try:
            while sock.h2_keep_connection:
                # Receive and send data
                self.receive_h2_data(sock,)
                self.send_h2_data(sock,)
        
        except ProtocolError as e:
            logger.log(f"Protocol Error: {e}", level=logger.WARNING)
            logger.log_exception(e)
            
        except Exception as e:
            logger.log(f"HTTP/2 Error: {e}", level=logger.WARNING)
            logger.log_exception(e)
            
        finally:
            sock.h2_keep_connection = False
            # Send goaway and close connection
            self.send_goaway(sock, 0)
    
    def receive_h2_data(self, sock):
        """
        Receive data that needs to be received from transport endpoint
        """
        try:
            self._receive_h2_data(sock)
        except socket.timeout:
            pass
            
    def send_h2_data(self, sock):
        """
        Sends data that needs to be sent to transport endpoint.
        """
        # Send data that needs to be sent
        data_to_send = sock.h2_connection.data_to_send()
            
        if data_to_send:
             try:
                 response_handler.send_data(
                     data_to_send,
                     sock, suppress_errors=False)
             except ssl.SSLEOFError:
                  # Suppress error: EOF occurred in violation of protocol (_ssl.c:2417)
                  pass
            
    def send_goaway(self, sock, error_code, debug_message: bytes = None):
        """Send a GOAWAY frame with the given error code and debug_message."""
        sock.h2_keep_connection = False
        
        if sock.h2_connection.state_machine.state == ConnectionState.CLOSED:
            self.close_socket(sock)  # close socket just to make sure
            return
        
        try:
            h2_connection = sock.h2_connection
            last_stream_id = h2_connection.highest_inbound_stream_id
            
            # Close and send GOAWAY
            h2_connection.close_connection(
                error_code,
                additional_data=debug_message or b""
            )
            sock.sendall(h2_connection.data_to_send())
        
        except (BrokenPipeError, ConnectionResetError):
            # Client closed connection, don't log this error
            pass
            
        except Exception as e:
            # Client might have terminated the connection
            if not "EOF occurred in violation of protocol" in str(e):
                # Log error only if its not "EOF occurred in violation of protocol" Error
                logger.log_raw(f"Error sending GOAWAY: {e}", level=logger.WARNING)
            
        finally:
            self.close_socket(sock)  # close socket immediately
    
    def _receive_h2_data(self, sock):
        """
        Receive data that needs to be received from transport endpoint
        """
        receive_timeout = SETTINGS["HTTP_2_RECEIVE_TIMEOUT"]
        default_timeout = sock.gettimeout()
        
        if receive_timeout:
            sock.settimeout(receive_timeout)
            try:
                data = sock.recv(SERVER_BUFFER)
            finally:
                sock.settimeout(default_timeout)
        else:
            data = sock.recv(SERVER_BUFFER)
        
        if not data:
            # No data, we are done
            sock.h2_keep_connection = False
            return
        
        # Retrieve events and dispatch them
        events = sock.h2_connection.receive_data(data)
        sock.h2_event_handler.dispatch_events(events)
        