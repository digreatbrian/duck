"""
Module containing server classes.
"""
import socket

from typing import Dict, Optional, Tuple

from duck.etc.ssl_defaults import SSL_DEFAULTS
from duck.settings import SETTINGS
from duck.exceptions.all import SettingsError
from duck.http.core.httpd.httpd import BaseMicroServer, BaseServer
from duck.http.core.httpd.http2 import BaseHttp2Server
from duck.utils.object_mapping import map_data_to_object
from duck.utils.sockservers import (
    Socket,
    SSLSocket,
    xsocket,
)


SUPPORT_HTTP_2 = SETTINGS["SUPPORT_HTTP_2"]

BaseServer = BaseHttp2Server if SUPPORT_HTTP_2 else BaseServer


class BaseHttpServer(BaseServer):
    """
    BaseHttpServer class for handling requests.
    """

    __instances: int = 0

    def __init__(
        self,
        addr: Tuple,
        socket_obj: socket.socket,
        enable_ssl: bool = False,
        ssl_params: Optional[Dict] = None,
        application=None,
        uses_ipv6: bool = False,
        **kwargs,
    ) -> None:
        """
        Initialise the server

        Args:
                socket_obj (socket.socket): The server's socket object.
                enable_ssl (bool): Whether to use SSL
                ssl_params (Optional[Dict]): Dictionary containing ssl parameters to parse to SSLSocket..
                application (App | MicroApp): The application that is using this server. Can be either duck main app or micro app.
                **kwargs: Extra keyword arguments like `poll`, `connection_mode`, `request_timeout` and `buffer`.
        """
        from duck.app.app import App
        from duck.app.microapp import MicroApp

        self.addr = addr
        self.enable_ssl = enable_ssl
        self.ssl_params = ssl_params or {}
        self.application = application
        self.uses_ipv6 = uses_ipv6

        assert isinstance(
            addr, tuple), "Argument addr should be an instance of tuple"
        assert len(addr) == 2, "Argument addr should be a tuple of length 2"
        assert isinstance(addr[0],
                          str), "Argument addr[0] should be an instance of str"
        assert isinstance(addr[1],
                          int), "Argument addr[1] should be an instance of int"
        assert enable_ssl in (
            True,
            False,
        ), "Argument enable_ssl should be a boolean"
        assert isinstance(
            self.ssl_params, dict
        ), f"Argument ssl_params should be an instance of dictionary, not {type(ssl_params)}"
        assert isinstance(
            application, (App, MicroApp)
        ), f"Argument application should be an instance of App or MicroApp, not {type(application)}"

        if not isinstance(socket_obj, (socket.socket, xsocket)):
            raise TypeError(
                f"Argument socket_obj should be an instance socket.socket, not {type(socket_obj)}"
            )

        # creating socket
        if enable_ssl:
            try:
                alpn_protocols = ["http/1.1", "http/1.0"]
                
                if SETTINGS['SUPPORT_HTTP_2']:
                    alpn_protocols.insert(0, "h2")
                
                self.sock = SSLSocket(
                    socket_obj=socket_obj,
                    server_side=True,
                    alpn_protocols=alpn_protocols,
                    **self.ssl_params)
                    
            except Exception:
                raise SettingsError(
                    "An error occurred whilst creating SSL socket, please make sure certfile and "
                    "private key exist and are in right format")
        else:
            self.sock = socket_obj or Socket(
                family=socket.AF_INET6 if uses_ipv6 else socket.AF_INET)
        
        self.running: bool = False
        self.__instances += 1
        map_data_to_object(self, kwargs)


class HttpServer(BaseHttpServer):
    """
    HttpServer class capable of handling unsecure http requests.
    """

    def __init__(
        self,
        addr: Tuple[str, int],
        application,
        uses_ipv6: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(
            addr=addr,
            socket_obj=Socket(family=socket.AF_INET6 if uses_ipv6 else socket.AF_INET),
            application=application,
            uses_ipv6=uses_ipv6,
        )


class HttpsServer(BaseHttpServer):
    """
    HttpsServer class capable of handling secure https requests.
    """

    def __init__(
        self,
        addr: Tuple[str, int],
        application,
        uses_ipv6: bool = False,
        **kwargs,
    ) -> None:
        default_ssl_params = SSL_DEFAULTS
        super().__init__(
            addr=addr,
            socket_obj=Socket(family=socket.AF_INET6 if uses_ipv6 else socket.AF_INET),
            enable_ssl=True,
            ssl_params=default_ssl_params,
            application=application,
            uses_ipv6=uses_ipv6,
        )


class MicroHttpServer(BaseMicroServer, HttpServer):
    """
    MicroHttpServer class for unsecure http based micro-servers.
    """

    def __init__(
        self,
        addr: Tuple[str, int],
        microapp,
        uses_ipv6: bool = False,
        **kwargs,
    ):
        self.set_microapp(microapp)
        super().__init__(addr, microapp, uses_ipv6=uses_ipv6)


class MicroHttpsServer(BaseMicroServer, HttpsServer):
    """
    MicroHttpsServer class for secure http(s) based micro-servers.
    """

    def __init__(
        self,
        addr: Tuple[str, int],
        microapp,
        uses_ipv6: bool = False,
        **kwargs,
    ) -> None:
        self.set_microapp(microapp)
        super().__init__(addr, microapp, uses_ipv6=uses_ipv6)
