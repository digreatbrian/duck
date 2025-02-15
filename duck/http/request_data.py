"""
Module containing a class for representing request data
"""
from typing import Dict


class RequestData:
    """
    RequestData class for storing headers and content/body.
    """
    def __init__(self, headers: Dict[str, str], content: bytes=b''):
        self.headers = headers
        self.content = content
    
    def __repr__(self):
        topheader=self.headers.get("topheader")
        return f'<{self.__class__.__name__} topheader: "{topheader}">'


class RawRequestData(RequestData):
    """
    This stores the request data as one body consisting of headers and content (in bytes)
    """
    def __init__(self, data: bytes):
        self.data = data
    
    def __repr__(self):
        topheader = self.data.split(b'\r\n', 1)[0]
        return f'<{self.__class__.__name__} topheader: "{topheader}">'
