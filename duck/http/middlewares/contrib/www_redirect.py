from duck.http.middlewares import BaseMiddleware
from duck.shortcuts import redirect
from duck.utils.urlcrack import URL
from duck.meta import Meta


class WWWRedirectMiddleware(BaseMiddleware):
    """
    Redirects all requests that start with `www` to non-www URL.
    """

    debug_message: str = (
        "WWWRedirectMiddleware: Redirecting to non-www domain")

    @classmethod
    def get_error_response(cls, request):
        """
        This is not actually an error response but a redirect to `non-www` URL
        """
        root_url = Meta.get_absolute_server_url()
        url = URL(root_url).innerjoin(request.fullpath).to_str()
        return redirect(url, permanent=True)

    @classmethod
    def process_request(cls, request):
        if request.host.startswith("www."):
            # Request is not actually bad but that's the only way to serve response immediately
            # without further processing.
            return cls.request_bad
        return cls.request_ok
