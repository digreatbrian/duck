"""
Duck-Django Middleware Integration

This module facilitates seamless data sharing between Duck and Django by providing 
middleware that processes and decompiles custom headers. It ensures that shared 
data is injected into Django's request `META` for consistent handling in Django views 
and middleware.

Key Components:
    - DuckMiddleware:
        A middleware class that processes and removes shared headers, restoring 
        them to Django's request `META`.
    - DJANGO_MIDDLEWARE:
        A dynamically imported middleware responsible for restoring HTTP requests 
        and managing shared data between Duck and Django.

Usage:
    Add `DuckMiddleware` to the `MIDDLEWARE` list in Django's settings to enable 
    this functionality. The integration relies on `DJANGO_MIDDLEWARE.restore_django_request`.

Dependencies:
    - `MiddlewareMixin`: Django's middleware base class for compatibility.
    - `x_import`: Utility for dynamic imports, used to load `DJANGO_MIDDLEWARE`.

Example:
    # settings.py
    MIDDLEWARE = [
        ...
        "duck.http.middlewares.DuckMiddleware",
        ...
    ]
"""
from django.contrib.sessions.middleware import MiddlewareMixin
from django.conf import settings
from duck.utils.importer import x_import


DJANGO_MIDDLEWARE = x_import("duck.http.middlewares.contrib.DjangoMiddleware")  
# Enables data sharing between Duck and Django.


class DuckMiddleware(MiddlewareMixin):
    """
    Middleware for processing and sharing custom headers between Duck and Django.

    This middleware is responsible for identifying and decompiling headers that 
    start with a specific prefix to facilitate seamless data sharing between 
    Duck's HTTP layer and Django's request handling. Shared headers are removed 
    from the original request headers after processing, and their corresponding 
    data is injected into Django's request `META`.

    Responsibilities:
        - Decompile and process headers with a specific prefix that indicate 
          shared data between Duck and Django.
        - Inject processed header data into Django's `META` dictionary, making 
          it accessible within Django views or middleware.
        - Safely discard unsupported header types to ensure stability.

    Notes:
        - Shared headers that do not match the expected format or have unsupported 
          data types will be discarded and will not be added to Django's request `META`.
        - This middleware depends on `DJANGO_MIDDLEWARE.restore_django_request` for 
          restoring and processing the request.

    Methods:
        - process_request(request):
            Restores and processes the incoming request to inject shared header 
            data into Django's request `META`.

    Usage:
        Add `DuckMiddleware` to the `MIDDLEWARE` list in your Django settings to 
        enable header processing and data sharing.

    Example:
        # settings.py
        MIDDLEWARE = [
            ...
            "duck.http.middlewares.DuckMiddleware",
            ...
        ]

    """

    def process_request(self, request):
        """
        Processes the incoming request to restore and decompile headers shared 
        between Duck and Django.

        Args:
            request (HttpRequest): The incoming HTTP request object.

        Workflow:
            1. Calls `DJANGO_MIDDLEWARE.restore_django_request` to process headers 
               and restore them to Django's request `META`.
            2. Removes processed headers from the original request object to 
               prevent redundancy or leakage of shared data.

        Returns:
            None: The method modifies the request object in place.
        """
        #duck_meta = DJANGO_MIDDLEWARE.resolve_meta_from_headers(request.headers) # This is the META that the Duck request has
        