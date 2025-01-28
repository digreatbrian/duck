"""
Utilities module for Django.
"""
from io import BytesIO
from django.http.response import (
    HttpResponse as DjangoHttpResponse,
    StreamingHttpResponse as DjangoStreamingHttpResponse,
)
from django.http.request import (
    HttpRequest as DjangoHttpRequest,
    RawPostDataException,
)
from duck.http.request import HttpRequest
from duck.http.response import (
    HttpResponse,
    StreamingHttpResponse,
)


def duck_url_to_django_syntax(url: str) -> str:
    """
    Converts a Duck URL path to Django's url path.

    Args:
        url (str): The URL path in duck syntax (e.g., /path/<some_variable>).

    Returns:
        str: The URL path in explicit Django syntax (e.g., /path/<str:some_variable>).
    """
    parts = url.split("/")
    output = []
    for part in parts:
        if "<" in part and ">" in part:
            # Replace the part with the converter syntax
            converter = "str"  # Default converter for strings
            var_name = part[part.find("<") + 1:part.find(">")]
            output.append(f"<{converter}:{var_name}>")
        else:
            output.append(part)
    return "/".join(output)


def duck_to_django_response(response: HttpResponse):
    """Converts Duck's http response to Django's http response object/"""
    headers = response.title_headers
    
    # Retrieve content type from headers or the automatic calculated content type
    content_type = response.get_header(
        'content-type',
        response.content_type,
    )
    if "Content-Type" in headers:
        # Django response doesn't allow setting both repsponse content_type arg and
        # also Content-Type header.
        headers.pop("Content-Type")
        
    if not isinstance(response, StreamingHttpResponse):
        return DjangoHttpResponse(
            content=response.content,
            status=response.status_code,
            headers=headers,
            content_type=content_type,
        )
    else:
        return DjangoStreamingHttpResponse(
            streaming_content=response.stream,
            status=response.status_code,
            headers=headers,
            content_type=content_type,
        )


def duck_to_django_request(request):
    """Converts Duck's HTTP request to Django's HttpRequest."""
    meta = request.META

    # Create a new Django HttpRequest object
    new_request = DjangoHttpRequest()
    new_request.method = request.method
    new_request.path = request.path
    new_request.META.update(meta)  # Copy META

    # Copy GET, POST, FILES data
    new_request.GET.update(request.GET)
    new_request.POST.update(request.POST)
    new_request.FILES.update(request.FILES)

    # Assign authentication and session data
    new_request.AUTH = request.AUTH
    new_request.session = request.SESSION
    
    # Check if 'request.raw' exists and is valid (adding a fallback in case it's missing)
    try:
        new_request._stream = BytesIO(request.raw)
    except AttributeError:
        new_request._stream = BytesIO()

    # Set request headers (handling case-insensitivity for headers)
    for h, v in request.headers.items():
        new_request.headers._store[h.lower()] = (h.title(), v)
    return new_request


def get_raw_django_payload(request: DjangoHttpRequest) -> bytes:
    """
    Retrieves the raw byte representation of the HTTP header section from a Django request.
    
    This function constructs the raw headers, starting with the request line (method, path, 
    protocol) and followed by all headers in the request, in the standard HTTP header format.

    Args:
        request (DjangoHttpRequest): The Django HTTP request object containing the request 
                                      and headers.

    Returns:
        bytes: A byte string representing the raw HTTP header section of the request, including 
               the request line and all headers. The result will be suitable for use in raw HTTP 
               request construction or logging.
    """
    # Start with the request line (method, path, protocol)
    topheader = f'{request.method} {request.path} {request.META.get("SERVER_PROTOCOL", "HTTP/1.1")}\r\n'
    raw = bytes(topheader, "utf-8")
    
    # Add headers to the raw request
    headers = request.headers
    for header, value in headers.items():
        # Ensure header title-cased and formatted correctly
        raw += bytes(header.title(), "utf-8") + b": " + bytes(value, "utf-8") + b"\r\n"
    return raw


def django_to_duck_request(django_request: DjangoHttpRequest):
    """
    Converts a Django request to a Duck request.
    """
    payload = get_raw_django_payload(django_request)
    new_request = HttpRequest()
    body = b''
    try:
        body = django_request.body
    except RawPostDataException:
        pass
    new_request.parse_raw_request(payload + b"\r\n")
    if hasattr(django_request, "user"):
        new_request.user = django_request.user
    return new_request
