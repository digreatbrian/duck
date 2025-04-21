"""
H2 Event handler module.
"""
import time
import asyncio

from typing import (
    Dict,
    Optional,
    List,
    Tuple,
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
from h2.exceptions import ProtocolError
from h2.errors import ErrorCodes
from h2.settings import SettingCodes

from duck.http.request_data import RequestData
from duck.http.response import HttpResponse
from duck.utils.caching import InMemoryCache
from duck.logging import logger


class EventHandler:
    """
    HTTP/2 Event handler (synchronous version).
    """
    def __init__(self, protocol):
        self.protocol = protocol
        self.conn = protocol.conn
        self.server = protocol.server
        self.stream_data = InMemoryCache()
        self.flow_control_futures = {}
        self.event_map = {
            RequestReceived: self.on_new_request,
            DataReceived: self.on_request_body,
            StreamEnded: self.on_request_complete,
            ConnectionTerminated: self.on_connection_terminated,
            StreamReset: lambda e: self.stream_reset(e.stream_id),
            WindowUpdated: lambda e: self.on_window_updated(e.stream_id, e.delta),
            RemoteSettingsChanged: self.on_remote_settings_changed,
        }

    def entry(self, data: bytes):
        """
        Entry method for processing incoming data.
        """
        try:
            events = self.conn.receive_data(data)
            self.dispatch_events(events)
        except ProtocolError as e:
            self.protocol.send_pending_data()
            self.protocol.close_connection(-1, str(e))
            
    def on_new_request(self, event):
        """
        Received headers for a new request.
        """
        stream_id = event.stream_id
        
        headers = {
            header.decode("utf-8"): value.decode("utf-8")
            for header, value in event.headers
        }
        request_data = RequestData(headers)
        self.stream_data.set(stream_id, request_data)
        
    def on_request_body(self, event):
        """
        Called when we received a request body.
        """
        stream_id = event.stream_id
        data = event.data

        stream_data = self.stream_data.get(stream_id)
        
        if not stream_data:
            self.conn.reset_stream(
                stream_id, error_code=ErrorCodes.PROTOCOL_ERROR
            )
        else:
            stream_data.content += data
            self.conn.increment_flow_control_window(5 * 1024 * 1024, stream_id)
            self.conn.acknowledge_received_data(len(data), stream_id)
            self.protocol.send_pending_data()
            
    def on_request_complete(self, event):
        """
        Full request received.
        """
        from duck.http.core.httpd.httpd import response_handler
        
        stream_id = event.stream_id
        request_data = self.stream_data.get(stream_id, pop=True)
        
        if not request_data:
            return
        
        # Create headers
        headers = request_data.headers
        topheader = "{method} {path} {http_version}".format(
            method=headers.pop(':method'),
            path=headers.pop(':path'),
            http_version='HTTP/2'
        )
        
        if ":authority" in headers:
            authority = headers.pop(':authority')
            headers["host"] = authority
        
        if ":scheme" in headers:
            headers.pop(":scheme")
            
        #: Important
        # Set the request data topheader in headers
        request_data.headers["topheader"] = topheader
        
        # Set request data stream ID
        request_data.request_store["stream_id"] = stream_id
        
        self.protocol.server.failsafe_process_and_handle_request(
            self.protocol.sock,
            self.protocol.addr,
            request_data,
        )
        
    def on_window_updated(self, stream_id: int, delta: int):
        """
        A window update frame was received.
        """
        if stream_id and stream_id in self.flow_control_futures:
            f = self.flow_control_futures.pop(stream_id)
            f.set_result(delta)
        elif not stream_id:
            for f in self.flow_control_futures.values():
                f.set_result(delta)
            self.flow_control_futures = {}
        
    def on_remote_settings_changed(self, event):
        """
        On RemoteSettingsChanged event handler method.
        """
        if SettingCodes.INITIAL_WINDOW_SIZE in event.changed_settings:
            self.on_window_updated(None, 0)
            
    def on_connection_terminated(self, event):
        """
        Connection terminated.
        """
        for future in self.flow_control_futures.values():
            future.cancel()
        self.flow_control_futures = {}
        self.protocol.connection_lost()
        
    def stream_reset(self, stream_id: int):
        """
        Stream reset received.
        """
        if stream_id in self.flow_control_futures:
            future = self.flow_control_futures.pop(stream_id)
            future.cancel()
        
    async def wait_for_flow_control(self, stream_id: int):
        """
        Waits for a Future that fires when the flow control window is opened.
        
        Args:
            stream_id (int): The HTTP/2 stream ID.
            
        """
        f = asyncio.Future()
        self.flow_control_futures[stream_id] = f
        await f
    
    def dispatch_events(self, events: List):
        """
        Dispatch all received events.
        """
        self.protocol.send_pending_data()
        
        for event in events:
            handler = self.event_map.get(type(event))
            
            if handler:
                handler(event)
            
            self.protocol.send_pending_data()
         