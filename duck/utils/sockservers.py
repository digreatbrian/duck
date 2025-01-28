"""
A simple implementation of socket servers.
"""

import socket
import ssl


def Socket(family=socket.AF_INET,
           sock_type=socket.SOCK_STREAM,
           **kw) -> socket.socket:
    """Returns a socket object with family and type stated as arguments."""
    return socket.socket(family, sock_type, **kw)


def SSLSocket(
    socket_obj: socket.socket,
    keyfile: str = None,
    certfile: str = None,
    version: int = ssl.PROTOCOL_TLS_SERVER,
    server_side: bool = True,
    ca_certs=None,
    ciphers=None,
) -> socket.socket:
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
    Returns:
        socket.socket: The secure SSL socket.
    """
    context = ssl.SSLContext(version)
    context.load_cert_chain(certfile=certfile, keyfile=keyfile)
    context.set_ciphers(ciphers) if ciphers else 0
    context.load_verify_locations(cafile=ca_certs) if ca_certs else 0
    return context.wrap_socket(socket_obj, server_side=server_side)
