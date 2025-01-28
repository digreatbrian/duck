"""
Module containing error classes.
"""


class BaseError(Exception):
    """Base class for all errors."""

    def __init__(self, message, **kws):
        """
        Stores the error message in the `message` attribute.

        Args:
            message (str): The error message.
            **kws: Additional keyword arguments.
        """
        self.message = message

    def __str__(self):
        """Returns the error message."""
        return f"{self.message}"


class ApplicationError(BaseError):
    """Represents base or micro app errors."""


class BlueprintError(Exception):
    """
    Raised for blueprint-related errors.
    """


class PortError(BaseError):
    """Raised for port obtaining errors."""


class RequestError(BaseError):
    """Raised for request errors."""


class RequestHostError(RequestError):
    """Raised for request host errors."""


class MethodNotAllowedError(RequestError):
    """Raised for request disallowed methods."""


class RequestSyntaxError(RequestError):
    """Raised for request syntax errors.."""


class RequestUnsupportedVersionError(RequestError):
    """Raised for unsupported http version."""


class RequestTimeoutError(RequestError):
    """Raised for request timeouts"""


class HeaderError(BaseError):
    """Raised for errors related to headers."""


class RouteError(BaseError):
    """Raised for errors related to routes."""


class RouteNotFoundError(BaseError):
    """Raised for errors related to unregistered routes."""


class FunctionError(BaseError):
    """Raised for errors related to functions."""


class CustomHeadersJsonLoadError(BaseError):
    """Raised when there's an error loading custom headers from JSON."""


class MiddlewareError(BaseError):
    """Raised when there's an error on any middleware"""


class MiddlewareLoadError(MiddlewareError):
    """Raised when there's an error loading or importing a middleware."""


class NormalizerError(BaseError):
    """Raised when there's an error on any normalizer"""


class NormalizerLoadError(NormalizerError):
    """Raised when there's an error loading or importing a normalizer."""


class CSRFMiddlewareError(MiddlewareError):
    """Raised when there's an error in CSRF middleware"""


class NormalizationError(BaseError):
    """Raised when there's an error in normalization process"""


class SettingsError(BaseError):
    """Raised for errors in the app's settings configuration."""


class ContentError(BaseError):
    """Raised for error related to setting Content of an HttpResponse."""


class TemplateError(BaseError):
    """Raised for any errors related to templates"""


class DjangoTemplateError(TemplateError):
    """Raised for error trying to use DjangoTemplateResponse if USE_DJANGO has been set to False in settings.py"""


class SSLError(BaseError):
    """
    Raised when ssl certfile or ssl private key is not found in locations specified in settings.py if and only if
    ENABLE_HTTPS=True
    """


class MultiPartParserError(BaseError):
    """
    Exception when parsing multipart/form-data
    """
