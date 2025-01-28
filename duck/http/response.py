"""
Module for representing Duck HttpResponses
"""
import io
import re
import os
import importlib

from datetime import datetime, timedelta
from collections.abc import Iterable
from typing import (
    Dict, Optional,
    Union, List,
    Callable, Tuple, Any,
)

from duck.http.content import Content
from duck.http.headers import Headers
from duck.http.request import HttpRequest
from duck.http.response_payload import (
    BaseResponsePayload,
    HttpResponsePayload,
)
from duck.template.environment import (
    Engine,
    Template,
)
from duck.etc.statuscodes import responses
from duck.utils.string import smart_truncate


StreamingType = Union[
    Callable[[], Union[bytes, str]],
    io.IOBase,
    Iterable[Union[bytes, str]]
]


# Dynamically load the standard library module `http.cookies`
# This is done to avoid using the duck.http module.
cookies_module = importlib.import_module("http.cookies")


# Use the module as usual
SimpleCookie = cookies_module.SimpleCookie


class FileIOStream(io.IOBase):
    """
    A custom class that mimics io.IOBase and streams file content efficiently.

    This class allows you to interact with a file as an IOBase stream. You can read
    file content in chunks and use seek/tell functionality to navigate through the file.
    """

    def __init__(self, filepath: str, chunk_size: int = 2 * 1024 * 1024):
        """
        Initializes the FileIOStream object with a file path and chunk size.

        Args:
            filepath (str): The path to the file to stream.
            chunk_size (int, optional): The size of each chunk to read. Default is 2MB.
        """
        self.filepath = filepath
        self.chunk_size = chunk_size
        self._file = None
        self._pos = 0  # Track the current position in the file
        self._file_size = os.path.getsize(filepath)  # Store file size for possible range support

    def _open(self):
        """Open the file for reading in binary mode."""
        if self._file is None:
            self._file = open(self.filepath, "rb")

    def read(self, size=-1):
        """
        Reads up to `size` bytes from the file. If `size` is negative, reads the entire file.
        
        Args:
            size (int): The number of bytes to read. If -1, read the entire file.
        
        Returns:
            bytes: A chunk of the file content.
        """
        self._open()

        if size == -1:
            content = self._file.read()  # Read the remaining content
        else:
            content = self._file.read(min(size, self.chunk_size))  # Read up to `size`

        # Update the position
        self._pos += len(content)
        return content

    def seek(self, offset, whence=0):
        """
        Move the file pointer to a specific position.
        
        Args:
            offset (int): The position to move to.
            whence (int): The reference point for offset (0: beginning, 1: current position, 2: file end).
        
        Returns:
            None
        """
        self._open()
        self._file.seek(offset, whence)
        self._pos = self._file.tell()

    def tell(self):
        """
        Returns the current position of the file pointer.
        
        Returns:
            int: The current position in the file.
        """
        return self._pos

    def close(self):
        """Closes the file stream."""
        if self._file is not None:
            self._file.close()
            self._file = None

    def __del__(self):
        """Ensure the file is closed when the object is deleted."""
        self.close()


class BaseResponse:
    """Response object to represent raw response"""

    def __init__(
        self,
        payload_obj: HttpResponsePayload,
        content_obj: Optional[Content] = None,
    ):
        """'
        Initialize Response object

        Args:
            payload_obj (HttpResponsePayload): Response Header object to represent Header
            content_obj (Optional[Content]): Content object.
        """
        assert isinstance(payload_obj, BaseResponsePayload), (
            f"Expected payload type 'BaseResponsePayload', but got '{type(payload_obj).__name__}'"
        )
        self.payload_obj: BaseResponsePayload = payload_obj
        self.content_obj: Content = content_obj or Content(b"")
        self.set_content_type_header()
    
    @property
    def cookies(self) -> SimpleCookie:
        """
        Property getter for cookies. If not already initialized, it initializes the cookies.
        
        Returns:
            SimpleCookie: The cookies for the response.
        """
        return self.payload_obj.cookies
    
    @cookies.setter
    def cookies(self, cookies_obj: SimpleCookie) -> None:
        """
        Setter for cookies. Assigns a SimpleCookie object to the internal cookies attribute.
        
        Args:
            cookies_obj (SimpleCookie): The SimpleCookie object to set.
        """
        self.payload_obj.cookies = cookies_obj
    
    @property
    def raw(self) -> bytes:
        """
        Retrieve the raw response data as a bytes object.
    
        This method returns the full response content (including headers) in its raw byte form,
        which can be useful for processing non-text-based data or for
        low-level handling of the response.
    
        Returns:
            bytes: The raw byte representation of the response.
        """
        response = self.payload_obj.raw
        response += b"\r\n\r\n" if not response.endswith(b"\r\n") else b"\r\n"
        response += self.content or b""
        return response

    @property
    def content(self) -> bytes:
        """
        Returns the content for the response.
        """
        return self.content_obj.data

    @property
    def content_type(self) -> str:
        """
        Returns the content type for the response.
        
        Notes:
            - This is not retrieved from headers but directly from the content object.

        """
        return self.content_obj.content_type

    @property
    def content_length(self) -> int:
        """
        Returns the content length for the response.
        
        Notes:
            - This is not retrieved from headers but directly from the content object.
        """
        return self.content_obj.size

    @property
    def content_encoding(self) -> str:
        """
        Returns the content encoding for the response.
        
        Notes:
            - This is not retrieved from headers but directly from the content object.

        """
        return self.content_obj.encoding

    @property
    def headers(self) -> Headers:
        """Return the current response headers"""
        return self.payload_obj.headers

    @property
    def title_headers(self) -> dict:
        """
        Response headers in title format rather than small cased
        e.g. {'Connection': 'close'} rather than {'connection': 'close'}
        """
        return self.payload_obj.headers.titled_headers()

    @property
    def status(self) -> tuple[int, str]:
        """
        The status of the response

        Returns:
            status (tuple): Status code and status message for response
        """
        return self.payload_obj.status_code, self.payload_obj.status_message

    @property
    def status_code(self) -> int:
        """
        Return status code for the response.
        """
        return self.payload_obj.status_code

    @property
    def status_message(self) -> str:
        """
        Return the status message for the response
        """
        return self.payload_obj.status_message

    @property
    def status_explanation(self) -> str:
        """
        Return the status message explantion for the response
        """
        return self.payload_obj.explanation

    def set_multiple_cookies(self, cookies: Dict[str, Dict[str, Any]]) -> None:
        """
        Sets multiple cookies at once. Each cookie is specified by a dictionary of attributes.
        
        Args:
            cookies (Dict[str, Dict[str, Any]]): A dictionary where the key is the cookie name
                                                 and the value is another dictionary of cookie attributes.
        """
        for cookie_name, attributes in cookies.items():
            self.set_cookie(cookie_name, **attributes)

    def get_cookie(self, name: str) -> str:
        """
        Retrieves the value of a specific cookie by name.
        
        Args:
            name (str): The name of the cookie to retrieve.
        
        Returns:
            str: The cookie value, or an empty string if the cookie does not exist.
        """
        return self._cookies.get(name, '').value if name in self._cookies else ''

    def get_all_cookies(self) -> Dict[str, str]:
        """
        Retrieves all cookies as a dictionary.
        
        Returns:
            Dict[str, str]: A dictionary of all cookies, where the key is the cookie name and the value is the cookie value.
        """
        return {key: morsel.value for key, morsel in self._cookies.items()}
    
    def set_cookie(
        self,
        key: str,
        value: str = "",
        domain: Optional[str] = None,
        path: str = "/",
        max_age: Optional[Union[int, timedelta]] = None,
        expires: Optional[Union[datetime, str]] = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: Optional[str] = "Lax",
    ) -> None:
        """
        Set a custom cookie on the HttpResponse.
    
        Args:
            key (str): The name of the cookie (e.g., 'csrftoken').
            value (str): The value of the cookie (e.g., 'some_random_token').
            domain (Optional[str]): The domain to set for the cookie. Defaults to None.
            path (str): The path for the cookie. Defaults to '/' indicating the whole site.
            max_age (Optional[Union[int, timedelta]]): The maximum age of the cookie in seconds or as a timedelta object.
            expires (Optional[Union[datetime, str]]): The expiration date of the cookie. Defaults to None.
            secure (bool): Whether the cookie should only be sent over HTTPS connections. Defaults to False.
            httponly (bool): Whether the cookie should be inaccessible to JavaScript. Defaults to False.
            samesite (Optional[str]): The SameSite attribute for the cookie. Default is 'Lax'. Other possible values are 'Strict' or 'None'.
    
        Raises:
            ValueError: If an invalid value is provided for `samesite`.
        """
        self.payload_obj.set_cookie(
            key = key,
            value = value,
            domain = domain,
            path = path,
            max_age = max_age,
            expires = expires,
            secure = secure,
            httponly = httponly,
            samesite = samesite,
       )
       
    def delete_cookie(self, key: str, path: str = "/", domain: Optional[str] = None) -> None:
        """
        Delete a cookie from the HttpResponse by setting its expiration date to the past.
        This will prompt the client to remove the cookie.

        Args:
            key (str): The name of the cookie to delete.
            path (str): The path for which the cookie was set. Defaults to "/".
            domain (Optional[str]): The domain for which the cookie was set. Defaults to None.
        """
        self.payload_obj.delete_cookie(key, path, domain)
        
    def set_content_type_header(self):
        """
        Sets the 'Content-Type' header based on the current content type.
        
        This method retrieves the content type from the `content_obj` and sets 
        it as the 'Content-Type' header of the response. This informs the client 
        about the type of content being returned (e.g., 'text/html', 'application/json').
        
        Example:
            If the content type is 'application/json', this method will set the header 
            to 'Content-Type: application/json'.
        """
        self.set_header("content-type", self.content_obj.content_type)
    
    def set_header(self, header: str, value: str):
        """
        Updates/sets a response header.
        """
        self.payload_obj.set_header(header, f"{value}".strip())

    def get_header(self, header: str, default_value: Optional = None) -> Optional[str]:
        """
        Returns the case-insensitive header value or fallback to default value if not found.
        """
        return self.payload_obj.headers.get(header, default_value)
        
    def __repr__(self):
        return f"<{self.__class__.__name__} (" f"'{self.status_code}'" f")>"


class HttpResponse(BaseResponse):
    """
    Class representing an http response.
    """
    def __init__(
        self,
        content: Optional[Union[str, bytes]] = None,
        status_code: int = 200,
        headers: dict = {},
        content_type: Optional[str] = None,
    ):
        payload_obj = HttpResponsePayload()
        payload_obj.parse_status(status_code)

        payload_obj.headers.update(headers) # update payload headers
        content_type_header = payload_obj.get_header("content-type")
        
        if content_type and content_type_header:
            raise ValueError(
                "Content type cannot be specified both as an argument and in the headers. "
                "Please provide it in one place only: either as an argument or in the headers."
            )
        
        if content and isinstance(content, str):
            content = content.encode("utf-8")
        
        # set content object
        content_obj = Content(
            data=content,
            content_type=content_type or content_type_header,
        )
        super().__init__(payload_obj, content_obj)


class StreamingHttpResponse(HttpResponse):
    """
    Class representing an HTTP streaming response.
    
    This class allows for streaming large content, such as files or dynamically 
    generated data, in chunks instead of loading the entire content into memory 
    at once. This is particularly useful for handling large files like videos, 
    audio, or data streams.
    """
    
    def __init__(
        self,
        stream: StreamingType,
        status_code: int = 200,
        headers: Dict = {},
        content_type: Optional[str] = 'application/octet-stream',
        chunk_size: int = 2 * 1024 * 1024,
    ):
        """
        Initialize a streaming response object.
        
        Args:
            stream (StreamingType):
                The content to stream. This can either be:
                - A callable that returns bytes or string, which will be repeatedly called to fetch data (in which case, the chunking is handled by the callable itself).
                - A file-like object (e.g., an instance of `io.IOBase` such as a file) that supports reading. When using an IO object, the response will read from the object in chunks.
                - An iterable object which has chunks of data as bytes or a string.
            
            status_code (int):
                The HTTP status code (default is 200).
                
            headers (Dict):
                Additional response headers (default is an empty dictionary).
                
            content_type (Optional[str]):
                The MIME type of the content (e.g., 'application/octet-stream').
                
            chunk_size (int):
                The size of chunks in bytes used for reading from the file-like object. This argument is only relevant when the `content` is an IO object.
                A larger chunk size generally improves performance by reducing the number of I/O operations but consumes more memory during the process.
                The default value is 2MB (2 048 000 bytes).
                Common sizes are between 1 MB (1048576 bytes) and 4 MB (4194304 bytes), but it should be adjusted based on the specific use case and server capabilities.
                If the content is callable, this argument is ignored, and chunking must be handled by the callable itself.   
        """
        super().__init__(
            content=b"",
            status_code=status_code,
            headers=headers,
            content_type=content_type,
        )      
        self.chunk_size = chunk_size
        self.stream = stream
        
        # Store the content (which can be a callable or file-like object)
        if callable(stream):
            self.content_provider = stream
        elif isinstance(stream, Iterable):
            self.content_provider = lambda: stream
        elif isinstance(stream, io.IOBase):
            self.content_provider = lambda: self._read_from_file(stream, chunk_size)
        else:
            raise ValueError("Stream must be either a callable, iterable or a file-like object.")
        
    @classmethod
    def file_stream(cls, filepath: str, chunk_size: int = 2 * 1024 * 1024):
        """
        Streams the content of a file in chunks for efficient handling of large files.
        
        This method reads a file at the given path and yields its content in chunks. 
        Each chunk is of the size specified by `chunk_size` (default is 1024 bytes). 
        This is useful for serving large files without loading the entire file into memory, 
        which helps improve performance and reduces memory consumption.
        
        Args:
            filepath (str): The path to the file that should be streamed.
            chunk_size (int, optional): The size of each chunk in bytes. Defaults to 1024 bytes.
            
        Yields:
            bytes: A chunk of the file content as a byte string. The size of each chunk will 
                   be `chunk_size`, except possibly the last chunk which may be smaller.
        
        Example:
            # Example usage for a file stream:
            response = StreamingHttpResponse(StreamingHttpResponse.file_stream('large_file.txt'))
            
        Notes:
            - This method ensures that the file is opened and closed properly using a context manager.
            - The `yield` keyword ensures the file content is streamed lazily, making this method 
              efficient for large files.
        """
        with open(filepath, "rb") as file:
            while chunk := file.read(chunk_size):
                yield chunk
    
    @classmethod
    def file_io_stream(cls, filepath: str, chunk_size: int = 2 * 1024 * 1024):
        """
        Creates an IOBase-like stream from a file for efficient handling of large files.

        This method returns an object that mimics the behavior of an io.IOBase stream.
        The stream can be used to read file content in chunks, and it supports
        operations like `seek`, `tell`, and `read`. This is useful for streaming large
        files with minimal memory usage.

        Args:
            filepath (str): The path to the file that should be streamed.
            chunk_size (int, optional): The size of each chunk in bytes. Defaults to 2MB.

        Returns:
            FileIOStream: A custom stream object that behaves like io.IOBase.

        Example:
            # Example usage:
            stream = StreamingHttpResponse.file_io_stream('large_file.txt')
            response = StreamingHttpResponse(stream)
            
        Notes:
            - The file is opened lazily when the stream is accessed.
            - The `seek` and `tell` methods allow for random access to the file.
        """
        return FileIOStream(filepath, chunk_size)

    def _read_from_file(self, file_obj: io.IOBase, chunk_size: int = 2 * 1024 * 1024):
        """
        Helper method to read the content from a file-like object in chunks.
        
        Args:
            file_obj (io.IOBase): The file-like object to stream content from.
            chunk_size (int): The size of each chunk to stream (default is 8192 bytes).
        
        Yields:
            bytes: A chunk of data read from the file-like object.
        """
        while chunk := file_obj.read(chunk_size):
            yield chunk

    def iter_content(self):
        """
        This method makes the response iterable so that the content can be streamed in chunks.
        """
        return self.content_provider()

    def __repr__(self):
        return f"<{self.__class__.__name__} (" f"'{self.status_code}'" f") {repr(self.stream).replace('<', '[').replace('>', ']')}>"


class StreamingRangeHttpResponse(StreamingHttpResponse):
    """
    A subclass of StreamingHttpResponse designed to handle HTTP responses that 
    support partial content (range requests), allowing clients to request specific 
    byte ranges of the response content. This is useful for handling large files 
    and enabling features like resuming downloads or streaming media.

    Example:
        response = StreamingRangeHttpResponse(
            stream=my_file,
            start_pos=-1000,  # Last 1000 bytes
            chunk_size=1024,
        )
        return response
    """
    
    def __init__(
        self,
        stream: io.IOBase,
        status_code: int = 206,
        headers: Dict = {},
        content_type: Optional[str] = 'application/octet-stream',
        chunk_size: int = 2 * 1024 * 1024,
        start_pos: int = 0,
        end_pos: Optional[int] = -1,
    ):
        """
        Initialize StreamingRangeHttpResponse class.
        
        Args:
            stream (io.IOBase): The stream from which to read the response data. 
                                 It can be a file-like object or an in-memory stream.
            status_code (int): The HTTP status code to return. Defaults to 206 (Partial Content).
            headers (Dict): Additional HTTP headers to include in the response. Defaults to an empty dict.
            content_type (str): The MIME type of the response content. Defaults to 'application/octet-stream'.
            chunk_size (int): The number of bytes to send in each chunk. Defaults to 2MB (2 * 1024 * 1024 bytes).
            start_pos (int): The starting byte position for the range request. Defaults to 0, can also be a negative.
            end_pos (int): The ending byte position for the range request. Defaults to -1, meaning the entire stream is used.
        """
        
        # Validate and assign the stream and content type
        if not isinstance(stream, io.IOBase):
            raise ValueError("The 'stream' argument must be a file-like object (io.IOBase).")
        
        self._stream = stream
        
        # If end_pos is -1, calculate it based on the stream length
        if end_pos == -1:
            if hasattr(stream, 'seek') and hasattr(stream, 'tell'):
                stream.seek(0, io.SEEK_END)
                end_pos = stream.tell()
            else:
                raise ValueError("Stream must support seeking to determine end position.")
        
        # Handle negative start_pos (e.g., -n means starting from the last n bytes)
        if start_pos < 0:
            if hasattr(stream, 'seek') and hasattr(stream, 'tell'):
                stream.seek(0, io.SEEK_END)
                start_pos = stream.tell() + start_pos  # Calculate offset from the end of the stream
            else:
                raise ValueError("Stream must support seeking to handle negative start_pos.")
        
        self.start_pos = start_pos
        self.end_pos = end_pos
        
        # Initialize the base StreamingHttpResponse
        super().__init__(
            stream=self._get_stream(),
            status_code=status_code,
            headers=headers,
            content_type=content_type,
            chunk_size=chunk_size,
        )
        self.set_content_range_headers()
     
    def set_content_range_headers(self):
        """
        Sets the content range headers based on current content range.
        """
        self.set_header('Content-Range', f"bytes {self.start_pos}-{self.end_pos-1}/*")
        self.set_header('Content-Length', str(self.end_pos - self.start_pos))
        self.set_header('Accept-Ranges', 'bytes')

    @classmethod
    def extract_range(cls, range_header: str) -> Optional[Tuple[int, int]]:
        """
        Extracts the byte range from the 'Range' header in the response and validates the range.
    
        Args:
            range_header (dict): The HTTP response 'Range' header.
            
        Returns:
            Tuple[int, int] or None: A tuple of the form (start, end) representing the byte range,
                                      or None if no range is specified.
            
        Raises:
            ValueError: If the 'Range' header format is invalid or if the extracted range is invalid
                        (e.g., `start_pos > end_pos`).
        """
        if range_header is None:
            return None  # No range specified
        
        # Match standard byte ranges (e.g., bytes=1000-2000)
        match = re.match(r"bytes=(\d+)-(\d+)?", range_header)
        
        if match:
            start = int(match.group(1))  # Always present
            end = match.group(2)  # May be None
            
            if end is None:
                # If the end is not specified, the range is from 'start' to the end of the file
                return (start, -1)  # -1 means until the end of the file
            
            end = int(end)
            
            # Validate that start <= end
            if start > end:
                raise ValueError(f"Invalid byte range: start ({start}) cannot be greater than end ({end}).")
            
            return (start, end)
    
        # Handle the case for negative ranges (e.g., bytes=-5000)
        negative_range_match = re.match(r"bytes=(-\d+)", range_header)
        
        if negative_range_match:
            # For negative ranges, calculate start as the last 'n' bytes and end as the last byte
            last_bytes = int(negative_range_match.group(1))
            
            # If last_bytes is negative, it refers to the last n bytes of the file
            start = last_bytes  # Start is the negative value, referring to the last n bytes
            end = -1  # End is the last byte
            
            # Validate that start <= end (for negative ranges, start should be <= end)
            if start > end:
                raise ValueError(f"Invalid byte range: start ({start}) cannot be greater than end ({end}).")
            
            return (start, end)
    
        # Handle the case for "bytes=-" (request for the last n bytes)
        if range_header == "bytes=-":
            return (-1, -1)  # Represents the entire file or last part of it
        
        raise ValueError(f"Invalid Range header format: {range_header}")
    
    def _get_stream(self):
        """
        Generator that yields chunks of the stream, starting from start_pos and ending at end_pos.
        The stream will be read in chunks defined by `chunk_size`.
        """
        
        # Ensure the stream is seekable before seeking to the start position
        if hasattr(self._stream, 'seek') and hasattr(self._stream, 'tell'):
            self._stream.seek(self.start_pos)
        else:
            raise ValueError("Stream must support seeking to handle partial content.")

        # Yield data in chunks of chunk_size
        while self._stream.tell() < self.end_pos:
            chunk = self._stream.read(self.chunk_size)
            if not chunk:
                break  # No more data to read
            yield chunk

    def __repr__(self):
        return f"<{self.__class__.__name__} (" f"'{self.status_code}'" f") {repr(self._stream).replace('<', '[').replace('>', ']')}>"


class FileResponse(StreamingRangeHttpResponse):
    """
    Class representing an http file response
    """

    def __init__(
        self,
        filepath: str,
        headers: Dict = {},
        status_code: int = 200,
        content_type: Optional[str] = None,
        chunk_size: int = 2 * 1024 * 1024,
        start_pos: int = 0,
        end_pos: Optional[int] = -1,
    ):
        """
        Initializes a streaming HTTP response for serving a file. Determines whether to stream the file in chunks
        or as a single response based on its size and ensures appropriate headers and content type are set.
    
        Args:
            filepath (str): The path to the file to be streamed.
            headers (Dict, optional): Additional HTTP headers to include in the response. Defaults to an empty dictionary.
            status_code (int, optional): The HTTP status code for the response. Defaults to 200 (OK).
            content_type (Optional[str], optional): The MIME type of the response content. If not provided, it is inferred 
                                                    from the file's extension. Defaults to None.
            chunk_size (int, optional): The size of chunks (in bytes) for streaming the file. Defaults to 2 MB 
                                        (2 * 1024 * 1024 bytes). For files smaller than 5 MB, the entire file 
                                        will be streamed at once.
            start_pos (int): The starting byte position for the range request. Defaults to 0.
            end_pos (int): The ending byte position for the range request. Defaults to -1, meaning the entire stream is used.
    
        Raises:
            FileNotFoundError: If the specified file does not exist.
            ValueError: If the file path is invalid or inaccessible.
    
        Notes:
            - If `content_type` is not provided, it is automatically determined from the file type and updated in the
              response headers.
            - For files smaller than 5 MB, the file will be streamed as a single response by overriding the `chunk_size`.
    
        Example:
            ```python
            response = CustomFileStreamer(
                filepath="/path/to/file.txt",
                headers={"Content-Disposition": "attachment; filename=file.txt"},
                content_type="text/plain",
                chunk_size=8192,
            )
            ```
        """
        # For smaller files sizes < 5MB, the file will be streamed once.
        file_size = os.path.getsize(filepath)
        
        if file_size <= 5 * 1024 * 1024:  # 5 MB
            chunk_size = file_size
            
        super().__init__(
            stream=StreamingHttpResponse.file_io_stream(filepath),
            status_code=status_code,
            headers=headers,
            content_type=content_type,
            chunk_size=chunk_size,
            start_pos=start_pos,
            end_pos=end_pos,
        )
        if not content_type:  # content type was not provided
            self.content_obj.filepath = filepath  # sets the content filepath
            self.content_obj.parse_type(None)  # recalculate the content_type using the set filepath
            self.set_content_type_header()  # resets content type header


class HttpRedirectResponse(HttpResponse):
    """
    Class representing an http redirect response.
    """

    def __init__(
        self,
        location: str,
        headers: Dict = {},
        content_type: Optional[str] = None,
        permanent: bool = False,
    ):
        headers = {"Location": "%s" % location, **headers}
        self.location = location
        status_code = 307  # temporary redirect

        if permanent:
            status_code = 301  # permanent redirect

        super().__init__("",
                         status_code,
                         headers=headers,
                         content_type=content_type)


class HttpErrorRequestResponse(HttpResponse):
    """
    Class epresenting an http error response.
    """

    def __init__(
        self,
        content: Optional[Union[str, bytes]] = None,
        status_code: int = 400,
        headers: Dict = {},
        content_type: Optional[str] = None,
    ):
        if not content:
            short_msg, content = responses.get(status_code,
                                               ("", "Sorry, Error In Request"))

        super().__init__(
            content,
            status_code,
            headers=headers,
            content_type=content_type,
        )


class HttpBadRequestResponse(HttpErrorRequestResponse):
    """
    Class representing an http bad request response.
    """

    def __init__(
        self,
        content: Optional[Union[str, bytes]] = None,
        headers: Dict = {},
        content_type: Optional[str] = None,
    ):
        status_code = 400

        super().__init__(content,
                         status_code,
                         headers=headers,
                         content_type=content_type)


class HttpForbiddenRequestResponse(HttpErrorRequestResponse):
    """
    Class representing an http forbidden request response.
    """

    def __init__(
        self,
        content: Optional[Union[str, bytes]] = None,
        headers: Dict = {},
        content_type: Optional[str] = None,
    ):
        status_code = 403

        super().__init__(content,
                         status_code,
                         headers=headers,
                         content_type=content_type)


class HttpBadRequestSyntaxResponse(HttpErrorRequestResponse):
    """
    Class representing an http bad request syntax response.
    """

    def __init__(
        self,
        content: Optional[Union[str, bytes]] = "Bad Request Syntax",
        headers: Dict = {},
        content_type: Optional[str] = None,
    ):
        status_code = 400

        super().__init__(content,
                         status_code,
                         headers=headers,
                         content_type=content_type)


class HttpUnsupportedVersionResponse(HttpErrorRequestResponse):
    """
    Class representing an http unsupported version response.
    """

    def __init__(
        self,
        content: Optional[Union[str, bytes]] = None,
        headers: Dict = {},
        content_type: Optional[str] = None,
    ):
        status_code = 505

        super().__init__(content,
                         status_code,
                         headers=headers,
                         content_type=content_type)


class HttpNotFoundResponse(HttpErrorRequestResponse):
    """
    Class representing an http not found response.
    """

    def __init__(
        self,
        content: Optional[Union[str, bytes]] = None,
        headers: Dict = {},
        content_type: Optional[str] = None,
    ):
        status_code = 404

        super().__init__(content,
                         status_code,
                         headers=headers,
                         content_type=content_type)


class HttpMethodNotAllowedResponse(HttpErrorRequestResponse):
    """
    Class representing an http method not allowed response.
    """

    def __init__(
        self,
        content: Optional[Union[str, bytes]] = None,
        headers: Dict = {},
        content_type: Optional[str] = None,
    ):
        status_code = 405

        super().__init__(content,
                         status_code,
                         headers=headers,
                         content_type=content_type)


class HttpServerErrorResponse(HttpErrorRequestResponse):
    """
    Class representing an http server error response.
    """

    def __init__(
        self,
        content: Optional[Union[str, bytes]] = None,
        headers: Dict = {},
        content_type: Optional[str] = None,
    ):
        status_code = 500

        super().__init__(content,
                         status_code,
                         headers=headers,
                         content_type=content_type)


class HttpBadGatewayResponse(HttpErrorRequestResponse):
    """
    Class representing an http bad gateway response.
    """

    def __init__(
        self,
        content: Optional[Union[str, bytes]] = None,
        headers: Dict = {},
        content_type: Optional[str] = None,
    ):
        status_code = 502

        super().__init__(content,
                         status_code,
                         headers=headers,
                         content_type=content_type)


class HttpTooManyRequestsResponse(HttpErrorRequestResponse):
    """
    Class to representing an http too many requests response.
    """

    def __init__(
        self,
        content: Optional[Union[str, bytes]] = "Too many requests",
        headers: Dict = {},
        content_type: Optional[str] = None,
    ):
        status_code = 400

        super().__init__(content,
                         status_code,
                         headers=headers,
                         content_type=content_type)


class HttpRequestTimeoutResponse(HttpErrorRequestResponse):
    """
    Class representing an http request timeout response.
    """

    def __init__(
        self,
        content: Optional[Union[str, bytes]] = None,
        headers: Dict = {},
        content_type: Optional[str] = None,
    ):
        status_code = 408

        super().__init__(content,
                         status_code,
                         headers=headers,
                         content_type=content_type)


class TemplateResponse(HttpResponse):
    """
    TemplateResponse class representing an http  template response.
    """

    def __init__(
        self,
        request: HttpRequest,
        template: str,
        context: Dict = {},
        status_code: int =200,
        headers: Dict = {},
        content_type: str = "text/html",
        engine: Optional[Engine] = None,
    ):
        self.template = template
        self.request = request
        self.context = context or {}
        self.engine = engine or ten
        self.context.update({"request": request})  # add request to context
        self.context.update({"template_engine":
                             "django"})  # add the template engine

        self._template = Template(
            name=template,
            context=context,
            engine=engine,
        )
        super().__init__(
            self._template.render_template(),
            status_code,
            headers=headers,
            content_type=content_type,
        )
