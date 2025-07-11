"""
Simple implementations of socket servers.
"""
import ssl
import socket
import _socket

from typing import Union


def patch_socket_recv(sock: socket.socket, buffer_size: int = 2048):
    """
    Monkey-patches the `recv` method of a socket object to internally use `recv_into` with a reusable buffer.

    This approach reduces the number of intermediate byte objects created during socket reads
    by reusing a single internal buffer for each `recv` call. The patched `recv` method signature
    remains the same as the original.

    Args:
        sock (socket.socket): The socket object to patch.
        buffer_size (int, optional): The size of the internal reusable buffer in bytes. Defaults to 2048.

    Returns:
        Callable: The original `recv` method before patching, which can be used to restore the socket's behavior.

    Notes:
        - The patched `recv` method still returns a new bytes object on each call, slicing the internal buffer.
        - For maximum performance gains, it is better to refactor code to use `recv_into` and `memoryview` directly.
        - This patch works best for blocking sockets. For non-blocking sockets, `BlockingIOError` is caught and zero bytes are returned.

    Example:
        >>> import socket
        >>> sock = socket.socket()
        >>> original_recv = patch_socket_recv(sock)
        >>> data = sock.recv(1024)
        >>> # Use original_recv to restore if needed
        >>> sock.recv = original_recv
    """
    buf = bytearray(buffer_size)

    original_recv = sock.recv

    def recv_patched(n: int = buffer_size, flags: int = 0) -> bytes:
        """
        Replacement for socket.recv that uses recv_into with a reusable buffer.

        Args:
            n (int): Maximum number of bytes to read. Limited internally by buffer_size.
            flags (int): Flags passed to the underlying recv_into call.

        Returns:
            bytes: Data read from the socket as a bytes object.
        """
        size_to_read = min(n, buffer_size)
        mv = memoryview(buf)
        try:
            count = sock.recv_into(mv[:size_to_read], flags)
        except BlockingIOError:
            # Non-blocking socket with no data available
            count = 0
        return bytes(buf[:count])

    sock.recv = recv_patched
    return original_recv


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
        
        Notes:
        - This also Monkey-patches the `recv` method of a socket object to internally use `recv_into` with a reusable buffer.
               This is done by calling `patch_socket_recv` function.
        """
        if not isinstance(sock, cls) and not isinstance(sock, ssl.SSLSocket):
            fd = socket.dup(sock.fileno())
            xsock = cls(sock.family, sock.type, sock.proto, fileno=fd)
            xsock.settimeout(sock.gettimeout())
            xsock.setblocking(sock.getblocking())
            xsock.original_recv = patch_socket_recv(xsock)
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
        version (int): SSL Protocol version.
        server_side (bool): Whether the socket is for the server side.
        ca_certs (str, optional): Path to trusted CA certificates.
        ciphers (str, optional): Cipher suites string.
        alpn_protocols (list, optional): ALPN protocols (e.g., ["h2", "http/1.1"]).

    Returns:
        xsocket: The secure SSL socket.
    """
    context = ssl.SSLContext(version)

    # Load cert and key
    if certfile and keyfile:
        context.load_cert_chain(certfile=certfile, keyfile=keyfile)

    # Set ciphers if provided
    if ciphers:
        context.set_ciphers(ciphers)

    # Load CA certs if provided
    if ca_certs:
        context.load_verify_locations(cafile=ca_certs)

    # Configure for HTTP/2 if needed
    if alpn_protocols and "h2" in alpn_protocols:
        # Use minimum_version instead of setting context.options
        if hasattr(context, "minimum_version"):
            context.minimum_version = ssl.TLSVersion.TLSv1_2
        else:
            context.options |= (
                ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 |
                ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
            )
        if hasattr(context, "options") and hasattr(ssl, "OP_NO_COMPRESSION"):
            context.options |= ssl.OP_NO_COMPRESSION

        try:
            context.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20")
        except ssl.SSLError:
            pass  # fallback to default if not supported

    # ALPN support
    if alpn_protocols:
        context.set_alpn_protocols(alpn_protocols)
    
    return context.wrap_socket(socket_obj, server_side=server_side)
