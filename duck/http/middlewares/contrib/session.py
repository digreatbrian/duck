"""
Module containing SessionMiddleware class.
"""

from duck.http.middlewares import BaseMiddleware
from duck.http.request import HttpRequest
from duck.meta import Meta
from duck.settings import SETTINGS


class SessionMiddleware(BaseMiddleware):
    """
    This middleware for creating and updating user sessions

    Notes:
        - This middleware is responsible for creating, updating and saving user sessions
        - Duck is lazy and it explicitly save the sessions on response bases (if session modified).
        - Request session should not be explicitly saved if you want session to be sent to the client in Set-Cookie header.
    """

    debug_message: str = "SessionMiddleware: Session error"

    @classmethod
    def process_response(cls, response, request):
        from duck.http.session.engine import SessionExpired
        
        if request.SESSION.needs_update(): # whether session has been modified.
            session_expired = False
            try:
                request.SESSION.save()
            except SessionExpired:
                session_expired = True
                request.set_expiry(
                    None
                )  # None will resolve to SESSION_AGE set in settings.py
                request.SESSION.save()
            
            if request.session_exists or session_expired:
                # No need of sending session cookie to the client because
                # the session key send by the client exists in our session storage.
                # Only send session key for newly created sessions or expired sessions.
                return
             
            session_key = request.SESSION.session_key
            session_cookie_name = SETTINGS["SESSION_COOKIE_NAME"]
            session_cookie_domain = SETTINGS[
                "SESSION_COOKIE_DOMAIN"] or Meta.get_metadata(
                    "DUCK_SERVER_DOMAIN")
            expire_at_browser_close = SETTINGS["SESSION_EXPIRE_AT_BROWSER_CLOSE"]
            expires = request.SESSION.get_expiry_date() if not expire_at_browser_close else None
            path = SETTINGS["SESSION_COOKIE_PATH"]
            secure = SETTINGS["SESSION_COOKIE_SECURE"]
            httponly = SETTINGS["SESSION_COOKIE_HTTPONLY"]
            samesite = SETTINGS["SESSION_COOKIE_SAMESITE"]
            
            if session_cookie_name in response.cookies:
                # Session cookie has been modified somehow, no need to set it
                return
                
            response.set_cookie(
                session_cookie_name,
                value=session_key,
                domain=session_cookie_domain,
                path=path,
                expires=expires,
                secure=secure,
                httponly=httponly,
                samesite=samesite,
            )
            
    @classmethod
    def process_request(cls, request: HttpRequest) -> int:
        """
        This processes the request and load/create user session

        Args:
                request (HttpRequest): The http request

        Returns:
            HttpRequestMiddleware.request_ok: Returns request_ok always
        """
        session_cookie_name = SETTINGS["SESSION_COOKIE_NAME"]
        session_key = request.COOKIES.get(session_cookie_name)
        session_exists = False

        if session_key:
            request.SESSION.session_key = session_key
            session_exists = False
            try:
                request.SESSION.load()
                if request.SESSION:
                    session_exists = True
            except KeyError:
                # session doesnt exist
                pass

        if not session_exists:
            # session needs to be created
            request.SESSION.create()
        request.session_exists = session_exists
        return cls.request_ok
