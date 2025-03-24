"""
Simple implementations of socket servers.
"""
import ssl
import socket
import _socket

from typing import Union


class xsocket(socket.socket):
    """
    Custom socket object which can store additional metadata.
    """
    @classmethod
    def from_socket(cls, sock):
        """
        Convert a socket object into an instance of the customizable xsocket class. 
        Unlike the built-in socket class, xsocket allows attribute manipulation.
    
        Args:
            sock (socket.socket or ssl.SSLSocket): 
                The socket object to be converted. If it is already an instance 
                of xsocket or ssl.SSLSocket, it is returned unchanged.
    
        Returns:
            xsocket: A new xsocket instance with the same properties as the original socket.
            If sock is already an xsocket or an ssl.SSLSocket, it is returned as is.
    
        Raises:
            TypeError: If sock is not an instance of socket.socket or ssl.SSLSocket.
        """
        if not isinstance(sock, cls) and not isinstance(sock, ssl.SSLSocket):
            fd = socket.dup(sock.fileno())
            xsock = cls(sock.family, sock.type, sock.proto, fileno=fd)
            xsock.settimeout(sock.gettimeout())
            xsock.setblocking(sock.getblocking())
            return xsock
        return sock


def Socket(
    family=socket.AF_INET,
    sock_type=socket.SOCK_STREAM,
    **kw) -> xsocket:
    """Returns a socket object with family and type stated as arguments."""
    return xsocket(family, sock_type, **kw)


def SSLSocket(
    socket_obj: Union[socket.socket, xsocket],
    keyfile: str = None,
    certfile: str = None,
    version: int = ssl.PROTOCOL_TLS_SERVER,
    server_side: bool = True,
    ca_certs=None,
    ciphers=None,
    alpn_protocols: list[str] = None,
) -> xsocket:
    """
    Return an SSL socket with the same arguments as `ssl.wrap_socket`.

    Args:
        socket_obj (socket.socket): The underlying socket object to secure.
        keyfile (str, optional): Path to the server's private key file (PEM format).
        certfile (str, optional): Path to the server's certificate file (PEM format).
        version (int): SSL Protocol version
        server_side (bool, optional): Whether the socket is being used on the server-side (True) or client-side (False). Defaults to True.
        ca_certs (str, optional): Path to a file containing trusted CA certificates (PEM format), used for server verification by the client.
        ciphers (str, optional): A colon-separated string specifying the supported ciphers.
        alpn_protocols (list, optional): List of protocols for ALPN (e.g., `["h2", "http/1.1"]`).
    
    Returns:
        xsocket: The secure SSL socket.
    """
    # Use create_default_context() for sensible default settings
    # context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    context = ssl.SSLContext(version)
    
    # Load the server's certificate and private key
    if certfile and keyfile:
        context.load_cert_chain(certfile=certfile, keyfile=keyfile)

    # Set cipher suites if provided
    if ciphers:
        context.set_ciphers(ciphers)

    # Set trusted CA certificates if provided
    if ca_certs:
        context.load_verify_locations(cafile=ca_certs)

    # If ALPN protocols are specified and "h2" is included for HTTP/2 support
    if alpn_protocols and "h2" in alpn_protocols:
        # RFC 7540 Section 9.2: Implementations of HTTP/2 MUST use TLS version 1.2
        context.options |= (
            ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
        )

        # RFC 7540 Section 9.2.1: Disable compression for HTTP/2
        context.options |= ssl.OP_NO_COMPRESSION

        # Restrict ciphers for HTTP/2 to the recommended suites
        context.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20")
    
    # Set ALPN protocols if provided
    if alpn_protocols:
        context.set_alpn_protocols(alpn_protocols)

    # Try to set NPN protocols if ALPN is not supported (though deprecated)
    try:
        context.set_npn_protocols(alpn_protocols) if alpn_protocols else None
    except Exception:
        pass
    
    # Wrap the socket with the configured SSL context
    return context.wrap_socket(socket_obj, server_side=server_side)
