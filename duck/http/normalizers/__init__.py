from duck.exceptions.all import NormalizationError
from duck.http.request import HttpRequest
from duck.utils.path import normalize_url_path


class URLNormalizer:
    """Class for normalizing URL in a request."""

    @classmethod
    def normalize(cls, request: HttpRequest):
        """This normalizes a URL in the request."""
        if not isinstance(request, HttpRequest):
            raise NormalizationError(
                f"HttpRequest object required, not '{type(request).__name__}'"
            )
        if request.path is not None:  # Ensure the path is not None
            request.path = normalize_url_path(request.path)
        else:
            request.path = ""
