"""
Module containing RequestsLimitMiddleware class for limiting number of
requests from same client within a specific duration.
"""

import random

from time import monotonic

from duck.http.middlewares import BaseMiddleware
from duck.settings import SETTINGS
from duck.shortcuts import simple_response, template_response
from duck.http.response import HttpTooManyRequestsResponse
        

class RequestsLimitMiddleware(BaseMiddleware):
    """
    Middleware for limiting the number of requests from a single IP address
    within a fixed time window.

    Tracks request timestamps per IP and rejects requests that exceed the
    allowed rate, preventing abuse or denial-of-service patterns.
    """

    _clients: dict[str, list[float]] = {}
    """In-memory store of request timestamps per client IP."""

    requests_delay: float = 2
    """Duration in seconds defining the time window for request counting."""

    max_requests: int = 15
    """Maximum number of allowed requests within the `requests_delay` window."""
    
    debug_message: str = "RequestsLimitMiddleware: Too many requests"
    
    @classmethod
    def _process_request(cls, request):
        """
        Processes the request by enforcing the rate limit logic.

        Args:
            request (HttpRequest): The incoming HTTP request object.

        Returns:
            str: `cls.request_ok` if allowed, else `cls.request_bad` for rate-limited clients.
        """
        now = monotonic()

        if request.client_address:
            ip, _ = request.client_address
            timestamps = cls._clients.get(ip, [])

            # Filter timestamps within the allowed window
            timestamps = [ts for ts in timestamps if now - ts < cls.requests_delay]

            if len(timestamps) >= cls.max_requests:
                return cls.request_bad

            timestamps.append(now)
            cls._clients[ip] = timestamps

            # Passive cleanup if too many IPs stored
            if len(cls._clients) > 10_000 and random.random() < 0.01:
                cls._cleanup_clients(now)

        return cls.request_ok

    @classmethod
    def _cleanup_clients(cls, now: float):
        """
        Performs a passive cleanup of expired request data from the `_clients` dict.

        Args:
            now (float): The current monotonic time used for expiry comparison.
        """
        threshold = now - cls.requests_delay
        cls._clients = {
            ip: [t for t in ts if t > threshold]
            for ip, ts in cls._clients.items()
            if any(t > threshold for t in ts)
        }

    @classmethod
    def get_readable_limit(cls) -> str:
        """
        Returns a human-readable description of the request rate limit.

        Returns:
            str: A string describing the maximum allowed requests per time window.
        """
        if cls.requests_delay == 1:
            return f"{cls.max_requests} requests per second"
        return f"{cls.max_requests} requests per {cls.requests_delay} seconds"

    @classmethod
    def get_error_response(cls, request):
        """
        Returns an appropriate error response for rate-limited clients.

        Args:
            request (HttpRequest): The incoming request.

        Returns:
            HttpResponse: A 429 (Too Many Requests) response.
        """
        if SETTINGS["DEBUG"]:
            body = (
                "<h4>Too Many Requests!</h4>"
                f"<p>Rate limit for {cls.__name__}: {cls.get_readable_limit()}.</p>"
                f"<p>Received more than {cls.max_requests} requests within the last {cls.requests_delay} seconds.</p>"
            )
            return template_response(HttpTooManyRequestsResponse, body=body)
        return simple_response(HttpTooManyRequestsResponse)

    @classmethod
    def process_request(cls, request):
        """
        Main entry point called by the Duck framework to process each request.

        Args:
            request (HttpRequest): The incoming HTTP request object.

        Returns:
            str: `cls.request_ok` or `cls.request_bad` based on request rate.
        """
        try:
            return cls._process_request(request)
        except Exception:
            return cls.request_ok
