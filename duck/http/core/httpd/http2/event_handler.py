"""
H2 Event handler module.
"""
import time
import asyncio
import threading

from typing import (
    Dict,
    Optional,
    List,
    Tuple,
    Callable,
)
from functools import partial
from concurrent.futures import Future
from asgiref.sync import iscoroutinefunction
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

from duck.settings import SETTINGS
from duck.http.request_data import RequestData
from duck.http.response import HttpResponse
from duck.utils.caching import InMemoryCache
from duck.logging import logger


class SyncFuture:
    """
    A thread-safe future that blocks until a result is set or an exception is raised.

    This class mimics a subset of the behavior of asyncio.Future, but for use in
    synchronous (threaded) code. It allows one thread to wait for a value or error
    that will be provided by another thread.
    """

    def __init__(self):
        """
        Initializes the SyncFuture with no result or exception.
        """
        self._event = threading.Event()
        self._result = None
        self._exception = None

    def set_result(self, value):
        """
        Sets the result of the future and unblocks any waiting thread.

        Args:
            value (Any): The result to return from the `result()` method.
        """
        self._result = value
        self._event.set()

    def set_exception(self, exception):
        """
        Sets an exception for the future and unblocks any waiting thread.

        Args:
            exception (Exception): The exception to raise when `result()` is called.
        """
        self._exception = exception
        self._event.set()

    def result(self):
        """
        Blocks until a result or exception is set, then returns or raises it.

        Returns:
            Any: The result value previously set by `set_result()`.

        Raises:
            Exception: If an exception was set using `set_exception()`.
        """
        self._event.wait()
        if self._exception:
            raise self._exception
        return self._result


class EventHandler:
    """
    HTTP/2 Event handler.
    
    This handles `h2` events asynchrously.
    
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

    async def entry(self, data: bytes):
        """
        Entry method for processing incoming data.
        """
        try:
            events = self.conn.receive_data(data)
            await self.dispatch_events(events)
        except ProtocolError as e:
            await self.protocol.async_send_pending_data()
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
        
    async def on_request_body(self, event):
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
            await self.protocol.async_send_pending_data()
            
    async def on_request_complete(self, event):
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
            http_version='HTTP/1.1'
        )
        
        if ":authority" in headers:
            authority = headers.pop(':authority')
            headers["host"] = authority
        
        if ":scheme" in headers:
            headers.pop(":scheme")
            
        #: Important
        # Set the request data topheader in headers
        request_data.headers["topheader"] = topheader
        
        # Set request data stream ID and h2_handling
        request_data.request_store["stream_id"] = stream_id
        request_data.request_store["h2_handling"] = True
        
        if SETTINGS['ASYNC_HANDLING']:
            # We are in async context
            await self.protocol.server.async_failsafe_process_and_handle_request(
                self.protocol.sock,
                self.protocol.addr,
                request_data,
            )
            
        else:
            # The server is using threads to manage the connection, so we need to dispose the processing of request
            # back to the current thread so that it will be handled synchronously rather than in async context.
            await self.execute_synchronously_in_current_thread(
                partial(
                    self.protocol.server.failsafe_process_and_handle_request,
                    self.protocol.sock,
                    self.protocol.addr,
                    request_data,
                )
            )
            
    async def execute_synchronously_in_current_thread(self, func: Callable):
        """
        Adds a callable to `sync_queue` so that it will be executed outside async context,
        useful in multithreaded environment where threads are created for each connection
        and `ASYNC_HANDLING=False`
        
        Args:
            func (Callable): Callable function or method which doesn't accept any arguments.
        """
        if not self.protocol.sync_queue:
            raise TypeError("Sync queue is not set, it is required for adding tasks to queue.")
        
        if SETTINGS['ASYNC_HANDLING']:
            raise SettingsError("ASYNC_HANDLING is set to True so no thread will be available to handle this task. Use sync_to_async to make this awaitable.")
        
        future = Future()
        self.protocol.sync_queue.put((func, future))
        
        # Wait for the synchrous task to finish without blocking event loop. 
        await self.protocol.event_loop.run_in_executor(None, future.result)
        
    def on_window_updated(self, stream_id, delta):
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
        
    def on_stream_reset(self, stream_id):
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
    
    def sync_wait_for_flow_control(self, stream_id: int):
        """
        Synchronously waits for a Future that fires when the flow control window is opened.
        
        Args:
            stream_id (int): The HTTP/2 stream ID.
            
        """
        f = SyncFuture()
        self.flow_control_futures[stream_id] = f
        f.result() # blocks until a result is set.
    
    async def dispatch_events(self, events: List):
        """
        Dispatch all received events.
        """
        await self.protocol.async_send_pending_data()
        
        for event in events:
            handler = self.event_map.get(type(event))
            
            if handler:
                if iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            await self.protocol.async_send_pending_data()
