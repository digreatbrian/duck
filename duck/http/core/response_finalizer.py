"""
Module containing ResponseFinalizer class focusing on putting on the final touches to the response.

The final touches include:
- Content compression.
- Content length calculation and insertion.
- Content encoding determination and insertion.
- etc.
"""

from duck.http.request import HttpRequest
from duck.http.response import (
    HttpResponse,
    StreamingHttpResponse,
    StreamingRangeHttpResponse,
    HttpRangeNotSatisfiableResponse,
)
from duck.logging.logger import (
    handle_exception as log_failsafe,
)
from duck.settings import SETTINGS
from duck.utils.dateutils import gmt_date
from duck.shortcuts import (
    replace_response,
    template_response,
    simple_response,
)


if SETTINGS["ENABLE_HTTPS"]:
    SECURITY_HEADERS = SETTINGS["SSL_SECURITY_HEADERS"]
else:
    SECURITY_HEADERS = SETTINGS["SECURITY_HEADERS"]


class ResponseFinalizer:
    """
    ResponseFinalizer class focusing on putting on the final touches to the response.
    """

    @log_failsafe
    def do_set_fixed_headers(self, response, request) -> None:
        """
        Sets fixed headers from settings, i.e. extra headers, cors headers and security headers.
        """
        extra = SETTINGS["EXTRA_HEADERS"] or {}
        cors = SETTINGS["CORS_HEADERS"] or {}
        security = SECURITY_HEADERS or {}

        for h, v in {**extra, **cors, **security}.items():
            response.headers.setdefault(h, v)

    @log_failsafe
    def do_set_connection_mode(self, response, request) -> None:
        """
        Sets the correct response connection mode, i.e. `keep-alive` or `close`.
        """
        connection_mode = None
        server_mode = SETTINGS["CONNECTION_MODE"].lower()

        if not request:
            response.set_header("Connection", "close")
            return

        if request.connection == server_mode:
            connection_mode = server_mode
        else:
            connection_mode = "close"
        response.set_header("Connection", connection_mode)

    @log_failsafe
    def do_content_compression(self, response, request) -> None:
        """
        Compresses the content if the client supports it and
        if the content is not a streaming response. (if necessary).
        """
        from duck.http.content import (
            COMPRESSION_ENCODING,
            COMPRESSION_LEVEL,
            COMPRESSION_MAX_SIZE,
            COMPRESSION_MIN_SIZE,
            CONTENT_COMPRESSION,
            COMPRESSION_MIMETYPES,
        )

        if not request or isinstance(response, StreamingHttpResponse):
            # We cannot compress content if we don't know whether the client supports it (via the 'Accept-Encoding' header).
            # Additionally, compression is not feasible for streaming HTTP responses because they are sent in chunks,
            # which makes it impossible to apply compression effectively beforehand.
            # Thus, we skip compression for streaming responses or when the client cannot accept compressed content.
            return

        if (not response.get_header("content-encoding", "identity") == "identity"
                or not response.content_obj.data.isascii()
                or response.content_obj.correct_encoding() != "identity"):
            # no need to compress content, might already be compressed
            return

        # check if content encoding is correctly set
        accept_encoding = request.get_header("accept-encoding", "").lower()
        supported_encodings = ["gzip", "deflate", "br", "identity"]

        if SETTINGS["ENABLE_CONTENT_COMPRESSION"]:
            if (COMPRESSION_ENCODING in accept_encoding
                    and COMPRESSION_ENCODING in supported_encodings):
                response.content_obj.compression_level = COMPRESSION_LEVEL
                response.content_obj.compression_min_size = (
                    COMPRESSION_MIN_SIZE)
                response.content_obj.compression_max_size = (
                    COMPRESSION_MAX_SIZE)
                response.content_obj.compression_mimetypes = (
                    COMPRESSION_MIMETYPES)
                compressed = response.content_obj.compress(
                    COMPRESSION_ENCODING)

                if compressed:
                    response.set_header("Content-Encoding", response.content_obj.encoding)
                else:
                    response.set_header(
                        "Content-Encoding",
                        response.content_obj.correct_encoding(),
                    )
        else:
            response.set_header(
                "Content-Encoding",
                response.content_obj.correct_encoding(),
           )

        if CONTENT_COMPRESSION.get("vary_on", False):
            # patch vary headers
            existing_vary_headers = response.get_header("Vary") or ""
            if existing_vary_headers:
                existing_vary_headers += ", "
            
            response.set_header(
                "Vary",
                existing_vary_headers + "Accept-Encoding",
            )

    @log_failsafe
    def do_set_content_headers(self, response, request) -> None:
        """
        Sets the appropriate content headers like Content encoding, type, etc.
        """ 
        if not response.get_header("content-length") and not isinstance(response, StreamingHttpResponse):
            # Don't set content length header if set or if it is a streaming http response.
            response.set_header("Content-Length", response.content_length)
        
        if not response.get_header("content-type"):
            content_type = response.content_type
            
            if isinstance(response, StreamingHttpResponse):
                content_type = "application/octet-stream" # default content type for streaming http responses.
                
            response.set_header("Content-Type", content_type)
        
        if not response.get_header("content-encoding"):
            response.set_header(
                "Content-Encoding",
                response.content_encoding 
                or response.content_obj.correct_encoding(),
           )

    @log_failsafe
    def do_set_extra_headers(self, response, request) -> None:
        """
        Sets last final extra headers like Date.
        """
        response.set_header("Date", gmt_date())

    @log_failsafe
    def do_set_streaming_range(self, response, request):
        """
        Set streaming range attributes on StreamingRangeHttpResponse. 
        This method parses the 'Range' header from the request and sets the 
        start and end positions for partial content streaming.
    
        Args:
            response (StreamingRangeHttpResponse): The response object to set streaming range on.
            request (HttpRequest): The incoming HTTP request containing the 'Range' header.
    
        Raises:
            ValueError: If the 'Range' header is malformed or invalid.
        """
        
        if not request:
            return  # If no request is provided, exit early.
    
        range_header = request.get_header('Range')
        
        if not range_header:
            if isinstance(response, StreamingRangeHttpResponse):
                if response.status_code == 206:
                    response.payload_obj.parse_status(200) # modify the response to correct status
                    response.clear_content_range_headers() # clear range headers
            return  # If no Range header exists, no need to set streaming range.
        
        if not isinstance(response, StreamingRangeHttpResponse):
            return
        
        try:
            # Extract start and end positions from the Range header
            start, end = StreamingRangeHttpResponse.extract_range(range_header)
            
            # Set the start and end positions on the response object
            response.parse_range(start, end)
            stream_size = response._stream.tell()
            
            if stream_size == (end-start):
                # This means full response
                if response.status_code == 206:
                    # Change response
                    response.parse_status(200)
                    response.clear_content_range_headers() # clear content range headers
                    return
            
            if end - start > 0:
                # Only set content length if result is greater than 1
                response.headers.setdefault("Content-Length", str(end-start))
            
        except ValueError:
            # replace response data
            new_response = None
            
            if SETTINGS["DEBUG"]:
                new_response = template_response(
                    HttpRangeNotSatisfiableResponse,
                    body=f"<p>Range is not satisfiable, could not resolve: {range_header}</p>")
            else:
                new_response = simple_response(HttpRangeNotSatisfiableResponse)
            
            # Replace response with new data
            replace_response(response, new_response)

    def finalize_response(self, response: HttpResponse, request: HttpRequest):
        """
        Puts the final touches to the response.
        """
        # All of the following method calls are failsafe meaning failure of any method
        # will not affect the execution of other methods, thus an error encountered will be
        # logged appropriately. Decorator responsible: @log_failsafe
        
        self.do_set_fixed_headers(response, request)
        self.do_set_connection_mode(response, request)
        self.do_content_compression(response, request)
        self.do_set_content_headers(response, request)
        self.do_set_extra_headers(response, request)
        self.do_set_streaming_range(response, request)
