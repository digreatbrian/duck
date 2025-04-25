"""
Module containing ResponseFinalizer class focusing on putting on the final touches to the response.

The final touches include:
- Content compression.
- Content length calculation and insertion.
- Content encoding determination and insertion.
- etc.
"""
import re

from typing import (
    Dict,
    Optional,
    Callable,
)

from duck.http.request import HttpRequest
from duck.http.response import (
    HttpResponse,
    FileResponse,
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
    to_response,
)
from duck.meta import Meta


# Custom templates for predefined responses
# This is a mapping of status codes to a response generating callable
CUSTOM_TEMPLATES: Dict[int, Callable] = SETTINGS["CUSTOM_TEMPLATES"] or {}

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
        
        content_security_policy = response.get_header("content-security-policy")
        
        if content_security_policy and request:
            domain = Meta.get_metadata("DUCK_SERVER_DOMAIN")
            
            if domain and domain != "localhost":
                scheme = request.scheme
                new_sources = f"{domain} www.{domain}"
        
                # Split CSP into directives
                directives = content_security_policy.strip().split(';')
                updated_directives = []
        
                default_updated = False
                for directive in directives:
                    directive = directive.strip()
                    if directive:
                        # Append new sources to existing default-src
                        updated = directive + " " + new_sources
                        updated_directives.append(updated)
                        default_updated = True
                    else:
                        updated_directives.append(directive)
        
                if not default_updated:
                    # If no default-src, add one
                    updated_directives.insert(0, f"default-src {new_sources}")
        
                # Rebuild CSP header
                final_policy = "; ".join(d.strip() for d in updated_directives if d) + ";"
                response.set_header("content-security-policy", final_policy)
        
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

        if response.content_obj.correct_encoding() != "identity":
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
            # Patch vary headers
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
        
        if not response.get_header("content-length") and isinstance(response, FileResponse):
            response.set_header("Content-Length", response.file_size)
            
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
         
        if not isinstance(response, StreamingRangeHttpResponse):
            return
        
        range_header = request.get_header('Range')
        
        if not range_header:
            if isinstance(response, StreamingRangeHttpResponse):
                if response.status_code == 206:
                    response.payload_obj.parse_status(200) # modify the response to correct status
                    response.clear_content_range_headers() # clear range headers
            return  # If no Range header exists, no need to set content range headers.
        else:
            if response.status_code == 200:
                # Invalid status (200 OK) instead of (206 Partial Content)
                response.payload_obj.parse_status(206) # modify the response to correct status
        try:
            # Extract start and end positions from the Range header
            # Note: Use response.start_pos & end_pos rather than start, end as they are the most recent offsets.
            start, end = StreamingRangeHttpResponse.extract_range(range_header)
            
            # Set the start and end positions on the response object
            stream_size = response.parse_range(start, end) # set content range headers (if applicable)
            
            # Set content length
            content_length = response.end_pos - response.start_pos
            
            if response.start_pos == response.end_pos:
                # If start_pos == end_pos, this mean that last byte will be required
                content_length = 1
                
            response.set_header("content-length", content_length)
            
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
            
            # Finalize response again as it has new values
            response.do_set_streaming_range = False # avoid max recursion error
            self.finalize_response(response, request)

    @log_failsafe
    def do_request_response_transformation(self, response: HttpResponse, request: HttpRequest):
        """
        Transforms the response object by applying request- and response-based modifications.
        
        This includes, but is not limited to, header changes and body alterations.
    
        Behavior Examples:
        - If the request method is `HEAD`, the response body is replaced with empty bytes.
        - If a matching template is found in the `CUSTOM_TEMPLATES` configuration, the entire response may be replaced.
    
        Args:
            response (HttpResponse): The original response to be transformed.
            request (HttpRequest): The incoming HTTP request associated with the response.
        """
        # Check if a custom template is configured for this response
        
        # Return the http response object.
        if request and str(request.method).upper() == "HEAD":
            # Reset content
            request.set_content(b"", auto_add_content_headers=True)
        
        if response:
            if response.status_code in CUSTOM_TEMPLATES:
                response_callable = CUSTOM_TEMPLATES[response.status_code]
                if not callable(response_callable):
                    raise TypeError(f"Callable required for custom template corresponding to status code of '{response.status_code}' ")
                
                # Parse parameters and obtain the custom template response.
                new_response = response_callable(
                    current_response=response,
                    request=request,
                )
                try:
                    new_response = to_response(new_response) # convert or check the validity of the custom response.
                except TypeError:
                    # The value returned by response_generating_callable is not valid
                    raise TypeError(f"Invalid data returned by the custom template callable corresponding to status code '{response.status_code}' ")
                
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
        self.do_request_response_transformation(response, request) 
        
        if hasattr(response, "do_set_streaming_range") and not response.do_set_streaming_range:
            return
            
        self.do_set_streaming_range(response, request)

