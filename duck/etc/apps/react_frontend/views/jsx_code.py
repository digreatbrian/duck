"""
Module containing view for serving jsx code dynamically.
"""
from duck.contrib.responses import template_response, simple_response
from duck.http.response import (
    HttpBadRequestResponse,
    HttpResponse,
)
from duck.settings import SETTINGS
from ..jsx_code_store import JsxCodeStore


def jsx_code_view(request):
    """
    A view for serving `JSX` code/content at a specific endpoint.
    
    This function provides a way to render and serve JSX content dynamically 
     using unique identifiers.
    
     Example:
     - Endpoint: `/react?id={id}`
       - `id` is a `SHA-256` unique identifier string representing the JSX content.
        
     Usage:
     - Register this view with a URL pattern to enable serving of JSX content 
       based on the provided identifier.
    """
    url_query = request.QUERY["URL_QUERY"]
    if 'id' in url_query:
         jsx_code_id = str(url_query['id'][0])
         jsx_code = JsxCodeStore.get_jsx_code(jsx_code_id)
         if jsx_code:
             return HttpResponse(content=jsx_code, content_type="text/babel")
    if SETTINGS["DEBUG"]:
         return template_response(HttpBadRequestResponse, body="The required URL query parameter 'id' is invalid or missing. Please ensure the 'id' parameter is included in the request and contains a valid value")
    return simple_response(HttpBadRequestResponse)
        