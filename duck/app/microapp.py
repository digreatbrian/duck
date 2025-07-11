"""
Mini application of Duck app which may be used for many simple tasks.

Notes:
- `Mini applications` run independently on their own individual ports.
- An example of a mini app is Duck's internal `HttpsRedirectApp` which is used to
	 redirect `http` traffic to a more secure https server.
"""
import threading

from typing import Union

from duck.settings import SETTINGS
from duck.http.core.httpd.servers import (
    MicroHttpServer,
    MicroHttpsServer,
)
from duck.http.core.processor import AsyncRequestProcessor, RequestProcessor
from duck.http.request import HttpRequest
from duck.http.response import (
    HttpRedirectResponse,
    HttpResponse,
)
from duck.contrib.sync import (
    convert_to_sync_if_needed,
    convert_to_async_if_needed
)
from duck.utils.net import is_ipv4
from duck.utils.port_recorder import PortRecorder
from duck.utils.urlcrack import URL


class MicroApp:
    """
    Duck micro app class to create a new lightweight sub-application/server

    This micro app can be used to create a new sub-application with its own server, meaning,
    you can create multiple micro apps in a single Duck application.

    Notes:
            - MicroApp should be used when you want to create a new server with its own address and port.
            - Every request to the micro app will be handled by the `view` method, no request will be passed to WSGI.
            - Everything is to be handled manually in the view method and none of all available middlewares will be applied.
    """

    all_threads: list = []
    """List of all threads created by initializing micro-application instances."""

    def __init__(
        self,
        addr: str = "localhost",
        port: int = 8080,
        enable_https: bool = False,
        parent_app=None,
        no_logs: bool = True,
        domain: str = None,
        uses_ipv6: bool = False,
    ):
        """
        Initialize the MicroApp class.
        
        Args:
            add (str): Micro application address, defaults to localhost.
            port (int): Micro application port. Defaults to 8080.
            enable_https (bool): Whether to enable `https`. Defaults to False.
            parent_app (Application): The root Duck application instance.
            no_logs (bool): Whether to log anything to console.
            domain (str): Micro application domain. Defaults to None.
            uses_ipv6 (bool): Whether to use `IPV6`. Defaults to False.
        """
        self.addr = addr
        self.port = port
        self.no_logs = no_logs
        self.parent_app = parent_app
        self.uses_ipv6 = uses_ipv6
        self.enable_https = enable_https
        
        # Set appropriate domain
        self.domain = domain or addr if not uses_ipv6 else f"[{addr}]"
        
        if is_ipv4(self.domain) and self.domain.startswith("0"):
            # IP "0.x.x.x" not allowed as domain because most browsers cannot resolve this.
            self.domain = "localhost"
        
        # Record port as used
        PortRecorder.add_new_occupied_port(port, f"{self}")

        if enable_https:
            self.server = MicroHttpsServer(
                microapp=self,
                addr=(addr, port),
                uses_ipv6=uses_ipv6,
            )
        else:
            self.server = MicroHttpServer(
                microapp=self,
                addr=(addr, port),
                uses_ipv6=uses_ipv6,
            )

        # creating vital threads without running them
        self.duck_server_thread = threading.Thread(
            target=self.server.start_server,
            args=[self.no_logs, domain]
        )
        type(self).all_threads.append(self.duck_server_thread)

    @property
    def absolute_uri(self) -> str:
        """
        Returns application server absolute `URL`.
        """
        scheme = "http"
        
        if self.enable_https:
            scheme = "https"
        
        uri = f"{scheme}://{self.domain}"
        uri = uri.strip("/").strip("\\")
        
        if not (self.port == 80 or self.port == 443):
            uri += f":{self.port}"
        
        return uri

    def build_absolute_uri(self, path: str) -> str:
        """
        Builds and returns absolute URL from provided path.
        """
        return URL.normalize_url(self.absolute_uri + "/" + path)

    @property
    def server_up(self) -> bool:
        """
        Checks whether the micro-application server is up and running.

        Returns:
            bool: True if up else False
        """
        return self.server.running
        
    def start_server(self):
        """
        Starts the Duck Server in a new thread.
        """
        self.duck_server_thread.start()

    def view(self, request: HttpRequest, processor: Union[AsyncRequestProcessor, RequestProcessor]) -> HttpResponse:
        """
        Entry method to response generation.

        Args:
            request (HttpRequest): The http request object.
            processor (Union[AsyncRequestProcessor, RequestProcessor]): Default request processor which you may use to process request.
        
        Notes:
        - Middlewares will not be applied on microapps, you are responsible for applying and handling middlewares.
        - On microapps, you are almost responsible for everything including managing database connections before and
          after request if needed.
        - But, the view response will be finalized automatically, meaning necessary headers will be set and response will be
          compressed if necessary.
        - When using `Asynchronous` mode, this method can be defined using `async def`. Duck will know how to deal with this.
        """
        raise NotImplementedError("Implement this method to return HttpResponse or any data as response.")

    def _view(self, request: HttpRequest, processor: RequestProcessor) -> HttpResponse:
        """
        Internal entry method to response generation.

        Args:
            request (HttpRequest): The http request object.
            processor (RequestProcessor): Default request processor which may be used to process request.
        """
        from duck.settings.loaded import WSGI
        response = convert_to_sync_if_needed(self.view)(request, processor)
        WSGI.finalize_response(response, request)  # finalize response
        return response

    async def _async_view(self, request: HttpRequest, processor: AsyncRequestProcessor) -> HttpResponse:
        """
        Internal entry method to asynchronous response generation.

        Args:
            request (HttpRequest): The http request object.
            processor (AsyncRequestProcessor): Default asynchronous request processor which may be used to process request.
        """
        from duck.settings.loaded import ASGI
        response = await convert_to_async_if_needed(self.view)(request, processor)
        await ASGI.finalize_response(response, request)  # finalize response
        return response

    def run(self):
        """
        Runs the duck sub-application.
        """
        self.start_server()

    def stop(self):
        """
        Stops the current running micro-application.
        """
        self.server.stop_server(log_to_console=not self.no_logs)


class HttpsRedirectMicroApp(MicroApp):
    """
    HttpsRedirectMicroApp class capable of redirecting http traffic to https.
    """

    def __init__(self, location_root_url: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.location_root_url = URL(location_root_url)
        
    def view(self, request: HttpRequest, request_processor: RequestProcessor) -> HttpResponse:
        """
        Returns an http redirect response.
        """
        from duck.settings.loaded import WSGI
        
        query = request.META.get("QUERY_STRING", "")
        dest_url = self.location_root_url.join(request.path)
        dest_url.query = query
        dest_url = dest_url.to_str()
        redirect = HttpRedirectResponse(location=dest_url, permanent=False)
        
        # Apply middlewares in reverse order
        WSGI.apply_middlewares_to_response(redirect, request)
        return redirect

    async def async_view(self, request: HttpRequest, request_processor: RequestProcessor) -> HttpResponse:
        """
        Returns an http redirect response.
        """
        from duck.settings.loaded import ASGI
        
        query = request.META.get("QUERY_STRING", "")
        dest_url = self.location_root_url.join(request.path)
        dest_url.query = query
        dest_url = dest_url.to_str()
        redirect = HttpRedirectResponse(location=dest_url, permanent=False)
        
        # Apply middlewares in reverse order
        await ASGI.apply_middlewares_to_response(redirect, request)
        return redirect


if SETTINGS['ASYNC_HANDLING']:
    HttpsRedirectMicroApp.view = HttpsRedirectMicroApp.async_view
