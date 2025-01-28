"""
Module containing RequestsLimitMiddleware class for limiting number of
requests from same client within a specific duration.
"""

from duck.contrib.responses import simple_response, template_response
from duck.http.middlewares import BaseMiddleware
from duck.http.response import HttpTooManyRequestsResponse
from duck.settings import SETTINGS
from duck.utils.caching import InMemoryCache


class RequestsLimitMiddleware(BaseMiddleware):

    _cache: InMemoryCache = InMemoryCache(maxkeys=1024 * 1024)
    """
	Cache for storing clients data.
	"""

    requests_delay: float | int = 1
    """
	Number of seconds to count before accepting client more of request(s).
	"""

    max_requests: int = 10
    """
	Max number of requests per specified client requests delay.
	"""

    debug_message: str = "RequestsLimitMiddleware: Too many requests"

    @classmethod
    def get_error_response(cls, request):
        if SETTINGS["DEBUG"]:
            body = f"<h4>Too Many Requests!</h4><p>Consider raising the number of  max requests or lowering requests delay for the {cls.__name__}.</p><p>Received more than {cls.max_requests} requests in {cls.requests_delay} seconds.</>"
            response = template_response(HttpTooManyRequestsResponse,
                                         body=body)
        else:
            body = None
            response = simple_response(HttpTooManyRequestsResponse)
        return response

    @classmethod
    def _process_request(cls, request):

        def reset_client_timer(ip):
            cls._cache.set(ip, {"current_requests": 1},
                           expiry=cls.requests_delay)

        if hasattr(request, "addr"):
            ip, port = request.addr
            data = cls._cache.get(ip)
            if not data:
                # reset timer
                reset_client_timer(ip)
            else:
                if data.get("current_requests", 0) >= cls.max_requests:
                    return cls.request_bad
        return cls.request_ok

    @classmethod
    def process_request(cls, request):
        try:
            return cls._process_request(request)
        except:
            pass
        return cls.request_ok
