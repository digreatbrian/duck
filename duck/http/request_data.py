"""
Module providing classes for representing and storing HTTP request data.
"""

from typing import Dict


class RequestData:
    """
    Represents a parsed HTTP request with headers and body content.

    This class is used to store and manage headers and raw body data extracted from
    an incoming HTTP request. It also includes a flexible `request_store` dictionary
    for attaching arbitrary metadata that can be used throughout request handling.
    """

    def __init__(self, headers: Dict[str, str], content: bytes = b''):
        """
        Initialize a new RequestData instance.

        Args:
            headers (Dict[str, str]): Dictionary of HTTP request headers.
            content (bytes, optional): Raw body content of the request. Defaults to b''.
        """
        self.headers = headers
        self.content = content
        self.request_store = {}  # A store for attaching additional metadata to this request instance.
    
    def __repr__(self):
        topheader = self.headers.get("topheader")
        return f'<{self.__class__.__name__} topheader: "{topheader}">'


class RawRequestData(RequestData):
    """
    Represents raw, unparsed HTTP request data as a single byte stream.

    This class stores the entire HTTP request (headers and body) as raw bytes,
    suitable for use in low-level HTTP request handling or custom parsing logic.
    """

    def __init__(self, data: bytes):
        """
        Initialize a new RawRequestData instance.

        Args:
            data (bytes): The full raw HTTP request in bytes, including headers and body.
        """
        self.data = data
        self.request_store = {}
    
    def __repr__(self):
        topheader = self.data.split(b'\r\n', 1)[0]
        return f'<{self.__class__.__name__} topheader: "{topheader.decode("utf-8", errors="ignore")}">'
