"""
Module for creating middlewares.
"""

from duck.http.request import HttpRequest
from duck.http.response import HttpBadRequestResponse, HttpResponse


class BaseMiddleware:
    """
    Base middleware class.

    Usage:
        - You can set and access class-specific attributes directly (e.g., `Middleware.{attrib}`).
        - Each subclass manages its own attributes independently, similar to how instances work.

    Notes:
        - Make sure the middleware class names are different for them to behave independently.
    """

    debug_message: str = "Middleware error"
    """
    Debug error message which may be logged to the console for debugging purposes.
    """

    request_ok: int = 1
    """Value to indicate if a request is in the correct format, has no errors, etc."""

    request_bad: int = 0
    """Integer to indicate if request has any kind of issues or errors."""

    _class_attrs = {}

    @classmethod
    def __setattr__(cls, key, value):
        if not hasattr(cls, "_class_attrs"):
            cls._class_attrs = {}
        if cls not in cls._class_attrs:
            cls._class_attrs[cls] = {}
        cls._class_attrs[cls][key] = value

    @classmethod
    def __getattr__(cls, key):
        if not hasattr(cls, "_class_attrs"):
            cls._class_attrs = {}
        if cls in cls._class_attrs and key in cls._class_attrs[cls]:
            return cls._class_attrs[cls][key]
        return getattr(type(cls), key, None)

    @classmethod
    def get_error_response(cls, request):
        """
        Returns the error response when process_request returns BaseMiddleware.request_bad.
        """
        error_response = HttpBadRequestResponse(
            "Sorry there is an error in Request, that's all we know!")
        return error_response

    @classmethod
    def process_request(cls, request: HttpRequest) -> int:
        """
        Processes the incoming request.
        """
        raise NotImplementedError(
            f"The method `process_request` should be implemented: {cls}")

    @classmethod
    def process_response(cls, response: HttpResponse,
                         request: HttpRequest) -> None:
        """
        Processes the outgoing response.
        """
