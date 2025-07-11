"""
Helpers for fast response generation.
"""

from typing import (
    Optional,
    Union,
    Dict,
    Any,
)

from duck.settings import SETTINGS
from duck.http.request import HttpRequest
from duck.http.response import (
    HttpBadGatewayResponse,
    HttpResponse,
    HttpServerErrorResponse,
    HttpMethodNotAllowedResponse,
    HttpNotFoundResponse,
    HttpBadRequestResponse,
    HttpBadRequestSyntaxResponse,
    HttpUnsupportedVersionResponse,
    HttpRequestTimeoutResponse,
)
from duck.shortcuts import (
    simple_response,
    template_response,
)
from duck.exceptions.all import (
    RequestSyntaxError,
    RequestUnsupportedVersionError,
)

from duck.meta import Meta
from duck.routes import RouteRegistry
from duck.logging import logger


# CSS style for debug error
debug_error_style = """
<style>
  h1 {
    color: #d32f2f; /* Deep red for error text */
  }
  .request-info .inner {
     background-color: #fdf2f2; /* Soft red background for better readability */
     border-radius: 4px;
     padding: 4px 4px;
     list-style: none;
  }
  .request-info .inner li {
    margin-left: 5px;
    color: #d32f2f; /* Deep red for error text */
  }
</style>	
"""
 
def get_debug_error_as_html(exception: Exception, request: Optional = None):
    """
    Returns the exception as html (only if DEBUG=True, else None).
    """
    def escape(content: str):
        """
        Returns escaped html content.
        """
        return content.replace("<", "&lt;").replace(">", "&gt;")
    
    if not SETTINGS["DEBUG"]:
        # return None immediately
        return
    
    # Expand exception  
    exception = logger.expand_exception(exception)
    
    # Make html from exception
    host = None # intialize host
    exception = escape(exception).replace("^\n", "^\n\n").replace("\n", "\n<br>")
    
    if not request:
       body = f"""
       <div class="request-info">
         <h4 class="subheading">Request</h4>
         <ul class="inner">Failed to retreive request metadata.</ul>
       </div><br><div class="exception">{exception}</div>
       """
       body = body + debug_error_style
       return body # return the body and style
    
    else:
      # Retrieve the original host
      if SETTINGS["USE_DJANGO"]:
          # If not real https host set, fallback to http host because this request might have been included inDUCK_EXPLICIT_URLS
          host = request.META.get("REAL_HTTP_HOST") or request.META.get("HTTP_HOST")
      
      else:
          host = request.META.get("HTTP_HOST")
      
      body = f"""
      <div class="request-info">
        <h4 class="subheading" >Request</h4>
        <ul class="inner">
          <li><p>Path: {request.path}</p>
          <li><p>Method: {request.method}</p>
          <li><p>Host: {host}</p>
          <li><p>HTTP-Version: {request.http_version if request.request_store.get("h2_handling") != True else "HTTP/2"}</p>
          <li><p>Content-Length: {request.content_obj.size}</p>
        </ul>
      </div><br><div class="exception">{exception}</div>
      """
      return body + debug_error_style


def get_timeout_error_response(timeout: Optional[Union[int, float]]) -> HttpRequestTimeoutResponse:
    """
    Returns the request timeout error response.
    
    Args:
        timeout (Union[int, float]): The timeout in seconds.
        
    """
    if SETTINGS["DEBUG"]:
        body = "<p>Client sent nothing in expected time it was suppose to!</p>"
        
        if timeout:
            body = "<p>Client sent nothing in expected time it was suppose to!</p><div>Timeout: ({timeout} seconds)</div>"
        
        response = template_response(
            HttpRequestTimeoutResponse,
            body=body,
        )
    else:
        response = simple_response(HttpRequestTimeoutResponse)


def get_server_error_response(exception: Exception, request: Optional = None):
    """
    Returns HttpServerError Response for the provided exception.
    """
    if request:
        request.META["DEBUG_MESSAGE"] = f"Internal Server Error: {request.path}"
    
    if SETTINGS["DEBUG"]:
        body = get_debug_error_as_html(exception, request)
        response = template_response(
            HttpServerErrorResponse,
            body=body,
        )
        return response
    else:
        response = simple_response(HttpServerErrorResponse)


def get_bad_gateway_error_response(exception: Optional[Exception], request: Optional = None):
    """
    Returns the appropriate Bad Gateway response.

    Args:
            exception (Optional[Exception]): The exception which might have caused this.
            The exception may be included in response.
            request (Optional): The current http request.
    """
    if request:
        request.META["DEBUG_MESSAGE"] = f"Bad Gateway: {request.path}"
    
    if SETTINGS["DEBUG"]:
        body = get_debug_error_as_html(exception, request)
        response = template_response(
            HttpBadGatewayResponse,
            body=body,
        )
    else:
        response = simple_response(HttpBadGatewayResponse)
    return response


def get_404_error_response(request: HttpRequest):
    """
    Returns HttpNotFoundError Response for the request.
    """
    if request:
        request.META["DEBUG_MESSAGE"] = f"Not Found: {request.path}"
    
    if SETTINGS["DEBUG"]:
        if request:
            body = f'<p>Specified URI not found: {request.path}</p>'
        else:
            body = f'<p>Specified URI not found</p>'
        
        if SETTINGS["USE_DJANGO"]:
            body += "<p>It seems like USE_DJANGO=True in settings, maybe this url is registered and only known to Django.</p>"
            body += "<p>You may add this url to DJANGO_SIDE_URLS if that is the case.</p>"
        
        # Add a list of registered routes
        body += "<h3>Duck tried the following routes</h3>"
        body += "<div class='registered-routes'>"
        
        for route, info in RouteRegistry.url_map.items():
            name = list(info.items())[0][0]
            
            # Replace < and > in route with allowed html signs (if present)
            route = route.replace('>', "&gt;").replace('<', "&lt;")
            
            body += f"""\n
            <div class='route' >
                <strong>{route}</strong> [name='{name}']
            </div>
            """
        
        # Close the div tag and add style
        body += "</div>"
        style = """
        <style>
           /* Other styles are derived from base_template_response.html */
            :root {
                --primary-color: #FF8C00;
            }
           div.registered-routes {
               border-radius: var(--border-radius);
               background-color: #fdf2f2; /* Soft red background for better readability */
               padding: 5px;
           }
           
            div.registered-routes .route {
                margin-top: 2px;
                color: var(--text-color);
            }
        </style>
        """
        body += style
        
        # Create an http template response
        response = template_response(
            HttpNotFoundResponse,
            body=body,
        )
    else:
        body = None
        response = simple_response(HttpNotFoundResponse, body=body)
    return response


def get_method_not_allowed_error_response(request: HttpRequest, route_info: Optional[Dict[str, Any]] = None):
    """
    Returns HttpMethodNotAllowed Response for the request.
    
    Args:
        request (HttpRequest): The http request.
        route_info (Optional[Dict[str, Any]]): The route info for the request obtained by RouteRegistry.
    """
    if request:
        request.META["DEBUG_MESSAGE"] = f"Method Not Allowed: {request.method}"
    
    if SETTINGS["DEBUG"]:
        if route_info:
            body = f'<p>Specified Method not allowed</p><div class="allowed-methods"> Allowed Methods: {[m.upper() for m in route_info["methods"]]}'
        else:
            body = "<p>Specified Method not allowed</p>"
        
        response = template_response(
            HttpMethodNotAllowedResponse,
            body=body,
        )
    else:
        body = None
        response = simple_response(HttpMethodNotAllowedResponse, body=body)
    return response


def get_bad_request_error_response(exception: Exception, request: Optional[HttpRequest] = None):
    """
    Returns HttpBadRequest Response for the request.
    
    Args:
        exception (Exception): The appropriate exception.
        request (Optional[HttpRequest]): The http request.
    """
    if request:
        request.META["DEBUG_MESSAGE"] = f"Bad Request: {request.path}"
    
    response_cls = HttpBadRequestResponse
    body = (
        "<p>Bad request, there is an error in request.</p><p>"
        "You might need to reconstruct request in right format</p>"
    )
    ref = f"<p>Ref: {exception}</p>"
    
    if isinstance(exception, RequestSyntaxError):
        response_cls = HttpBadRequestSyntaxResponse
        body = "<p>Bad request syntax.</p><p>You might need to reconstruct request in right format</p>"
        
        if request:
            request.META["DEBUG_MESSAGE"] = f"Bad Request Syntax: {request.path}"

    elif isinstance(exception, RequestUnsupportedVersionError):
        response_cls = HttpUnsupportedVersionResponse
        body = "<p>Unsupported http version.</p><p>You might need to switch to supported protocol.</p>"
        if request:
            request.META["DEBUG_MESSAGE"] = f"Unsupported HTTP Version: {request.http_version}"
    else:
        # General request error
        if "'utf-8' codec can't decode byte" in str(exception) and not SETTINGS['ENABLE_HTTPS']:
            # This might be a client sending https traffic to our http server
            response_cls = HttpBadRequestResponse
            body = "<p>Bad request, there is an error in request.</p><p>This might be a client sending https encrypted data to our http server.</p>"
            if request:
                request.META["DEBUG_MESSAGE"] = "Bad Request: Client might be trying to send HTTPs traffic to our HTTP server"
    
    if SETTINGS["DEBUG"]:
        response = template_response(response_cls, body=body + ref)
    else:
        body = None
        response = simple_response(response_cls, body=body)
    return response
