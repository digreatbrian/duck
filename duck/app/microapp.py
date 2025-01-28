"""
Mini application of Duck app which may be used for many simple tasks.

Notes:
	- Mini applications run independently on their own individual ports.
	- An example of a mini app is Duck's internal HttpsRedirectApp which is used to 
	redirect http traffic to a more secure https server.
"""

import threading
import urllib.parse

from duck.http.core.httpd.servers import MicroHttpServer, MicroHttpsServer
from duck.http.core.processor import RequestProcessor
from duck.http.request import HttpRequest
from duck.http.response import HttpRedirectResponse, HttpResponse
from duck.utils.path import sanitize_path_segment
from duck.utils.port_recorder import PortRecorder


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
        self.addr = addr
        self.port = port
        self.no_logs = no_logs
        self.parent_app = parent_app
        self.domain = domain
        self.uses_ipv6 = uses_ipv6

        PortRecorder.add_new_occupied_port(port,
                                           f"{self}")  # record port as used

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
            target=self.server.start_server, args=[self.no_logs, domain])
        type(self).all_threads.append(self.duck_server_thread)

    def start_server(self):
        """
        Starts the Duck Server in a new thread.
        """
        self.duck_server_thread.start()

    def view(self, request: HttpRequest,
             processor: RequestProcessor) -> HttpResponse:
        """
        Entry method to response generation.

        Args:
                request (HttpRequest): The http request object.
                processor (RequestProcessor): Default request processor which you may use to process request.
        """
        raise NotImplementedError(
            "Implement this method to return HttpResponse or any data as response."
        )

    def run(self):
        """
        Runs the duck sub-application.
        """
        self.start_server()

    def stop(self):
        """
        Stops the current running micro-application.
        """
        self.server.stop_server(log_to_console=False)


class HttpsRedirectMicroApp(MicroApp):
    """
    HttpsRedirectMicroApp class capable of redirecting http traffic to https.
    """

    def __init__(self, location_url: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.location_url = sanitize_path_segment(location_url)

    def view(self, request: HttpRequest,
             request_processor: RequestProcessor) -> HttpResponse:
        """
        Returns an http redirect response.
        """
        destination = urllib.parse.urljoin(self.location_url,
                                           request.path).rstrip("/")
        query = request.META.get("QUERY_STRING")
        if query:
            destination += "?" + query
        redirect = HttpRedirectResponse(location=destination, permanent=True)
        return redirect
