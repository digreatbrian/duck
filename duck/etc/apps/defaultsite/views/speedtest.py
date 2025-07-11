"""
Provides a default speed test view for Duck's site.

This view can be used to benchmark request-response times
and verify that the Duck HTTP stack is operational.
"""
from duck.http.request import HttpRequest
from duck.shortcuts import jsonify


def ducksite_speedtest_view(request: HttpRequest):
    """
    Returns a simple JSON response for speed testing.

    This endpoint is typically used by clients to measure
    basic response times and confirm server responsiveness.
    """
    return jsonify({"speed": "ok"})
