"""
Module containing CSRFMiddleware class which mitigates against Cross-Site-Request-Forgery (CSRF) attacks.
"""

import re
import os
import string
import secrets
import hashlib
import datetime
import urllib.parse

from duck.etc.internals.template_engine import InternalDuckEngine
from duck.http.middlewares import BaseMiddleware
from duck.http.request import HttpRequest
from duck.http.response import HttpForbiddenRequestResponse, TemplateResponse
from duck.meta import Meta
from duck.settings import SETTINGS
from duck.utils.safe_compare import constant_time_compare


CSRF_USE_SESSIONS = SETTINGS["CSRF_USE_SESSIONS"]

CSRF_SECRET_LENGTH = SETTINGS["CSRF_SECRET_LENGTH"]

CSRF_TOKEN_LENGTH = SETTINGS["CSRF_TOKEN_LENGTH"]

CSRF_SESSION_KEY = SETTINGS["CSRF_SESSION_KEY"]

# Allowed characters: Letters and Digits
ALLOWED_CHARACTERS = string.ascii_letters + string.digits


def generate_dynamic_secret_key() -> bytes:
    """
    Dynamically generates a secure, consistent key based on system-specific data.

    Returns:
        bytes: A dynamic, secure key derived from system-specific data.
    """
    # Use machine-specific information (e.g., os.urandom, hostname, or MAC address)
    machine_specific_data = os.getenv("HOSTNAME",
                                      "default_host").encode() + os.urandom(16)
    key = hashlib.sha256(machine_specific_data).digest()
    return key


def generate_csrf_secret() -> str:
    """
    Returns a secure random CSRF secret containing only letters and digits.
    """
    return "".join(
        secrets.choice(ALLOWED_CHARACTERS) for _ in range(CSRF_SECRET_LENGTH))


def mask_cipher_secret(secret: str) -> str:
    """
    Masks CSRF secret to produce a secure CSRF token.

    Args:
        secret (str): The CSRF secret.

    Returns:
        str: The CSRF token.

    Raises:
        ValueError: If the secret contains invalid characters.
    """
    if not all(char in ALLOWED_CHARACTERS for char in secret):
        raise ValueError(
            "Secret contains invalid characters. Only letters and digits are allowed."
        )

    # Generate a random mask of the same length as the secret
    mask = "".join(
        secrets.choice(ALLOWED_CHARACTERS) for _ in range(CSRF_SECRET_LENGTH))

    # XOR-like masking using modular arithmetic
    masked_secret = "".join(
        ALLOWED_CHARACTERS[(ALLOWED_CHARACTERS.index(secret[i])
                            + ALLOWED_CHARACTERS.index(mask[i]))
                           % len(ALLOWED_CHARACTERS)]
        for i in range(CSRF_SECRET_LENGTH))

    # Return the full token (mask + masked secret)
    return mask + masked_secret


def unmask_cipher_token(token: str) -> str:
    """
    Unmasks a CSRF token to retrieve the original CSRF secret.

    Args:
        token (str): The CSRF token.

    Returns:
        str: The original CSRF secret.

    Raises:
        ValueError: If the token is invalid or tampered with.
    """
    # Validate token length
    if len(token) != CSRF_TOKEN_LENGTH:
        raise ValueError("Invalid token length.")

    # Extract mask and masked secret
    mask = token[:CSRF_SECRET_LENGTH]
    masked_secret = token[CSRF_SECRET_LENGTH:]

    # Reverse the masking process to retrieve the original secret
    secret = "".join(
        ALLOWED_CHARACTERS[(ALLOWED_CHARACTERS.index(masked_secret[i])
                            - ALLOWED_CHARACTERS.index(mask[i]))
                           % len(ALLOWED_CHARACTERS)]
        for i in range(CSRF_SECRET_LENGTH))
    return secret


def add_new_csrf_cookie(request):
    """
    Generates a new CSRF secret and saves it in the request's metadata.

    Args:
        request: The HTTP request object.
        secret_key: The dynamic secret key used for signing the CSRF token.
    """
    csrf_secret = generate_csrf_secret()
    request.META["CSRF_COOKIE"] = csrf_secret
    request.META["CSRF_COOKIE_NEEDS_UPDATE"] = True
    return csrf_secret


def get_csrf_token(request):
    """
    Generates a new CSRF token and saves the CSRF secret in the request.META.

    Args:
            request: The http request.

    This function performs the following actions:
    1. Generates a new CSRF token (Csrf_Token), a scrambled/random token to be sent to the user.
    2. Saves the CSRF secret (Csrf_Secret) in:
       - request.META under the key 'CSRF_COOKIE'

    The CSRF token (Csrf_Token) is sent to the client each time this function is called. (This is done by CSRFMiddleware)
    """
    if "CSRF_COOKIE" in request.META:
        csrf_secret = request.META["CSRF_COOKIE"]
        # Since the cookie is being used, flag to send the cookie to client (even if the client already has it) in order to
        # renew the expiry timer.
        request.META["CSRF_COOKIE_NEEDS_UPDATE"] = True
    else:
        csrf_secret = add_new_csrf_cookie(request)
        # add_new_csrf_cookie adds these to request.META:
        #    1) CSRF_COOKIE
        #    2) CSRF_COOKIE_NEEDS_UPDATE
    try:
        csrf_token = mask_cipher_secret(csrf_secret)
    except Exception:
        # no substring found or csrf_secret is None
        # the csrf secret in request.META is invalid, add new one
        csrf_secret = add_new_csrf_cookie(request)
        csrf_token = mask_cipher_secret(csrf_secret)
    if CSRF_USE_SESSIONS:
        request.session[CSRF_SESSION_KEY] = csrf_secret
    return csrf_token


class OriginError(Exception):
    """
    Exception class for invalid HTTP Origin
    """


class RefererError(Exception):
    """
    Exception class for invalid HTTP Referer
    """


class CSRFCookieError(Exception):
    """
    Exception class for CSRF cookie errors.
    """


class CSRFMiddleware(BaseMiddleware):
    """
    Middleware for mitigating Cross-Site Request Forgery (CSRF) attacks.

    This middleware verifies the authenticity of requests by comparing the CSRF token 
    included in the request body (for methods such as POST, PUT, etc.) with the one 
    securely stored in the user's session (`request.SESSION`). This helps protect against
    unauthorized actions being performed using an authenticated user's session.

    The middleware operates with the following behavior:
    
    - **Conditional Activation:** When `USE_DJANGO=True`, this middleware is skipped 
      unless the request path corresponds to a Duck explicit URL. Duck explicit URLs 
      are listed in `DUCK_EXPLICIT_URLS` and should not be proxied to Django at any point.
    
    - **Prevention of CSRF Attacks:** CSRF attacks exploit a user's authenticated session 
      to perform unauthorized actions on their behalf. By ensuring the CSRF token in the 
      request body matches the one stored in the Session or Cookie, this middleware mitigates the risk 
      of such attacks.

    Attributes:
        USE_DJANGO (bool): Flag indicating whether to use Django for handling requests.
        DUCK_EXPLICIT_URLS (list): List of URLs that should be handled by Duck and not 
                                    proxied to Django.

    Methods:
        process_request(request): Verifies the CSRF token in the request and compares it 
                                  with the Csrf Cookie/Secret to ensure authenticity.

    """

    debug_message: str = "CsrfProtectionMiddleware: CSRF token missing or invalid"

    @classmethod
    @staticmethod
    def rotate_csrf_token(request: HttpRequest):
        """
        Resets the request csrf secret and returns the rotated csrf secret.
        """
        # rotate token after login, user may need to reload page to get new csrf_token
        csrf_secret = add_new_csrf_cookie(request)

    @classmethod
    def _check_origin_ok(cls, request):
        """
        Checks if request Origin is good origin

        Returns:
            True if request origin is ok

        Raises:
            OriginError: If origin provided is invalid in any way
        """
        request_origin = request.origin

        if not request_origin:
            raise OriginError("No Origin header found in request")

        good_origin = "%s://%s:%d" % (
            request.scheme,
            request.domain,
            request.port,
        )
        parsed_good_origin = urllib.parse.urlparse(good_origin)
        parsed_request_origin = urllib.parse.urlparse(request_origin)

        if parsed_request_origin.port:
            # there is port in origin header
            if parsed_request_origin.port != parsed_good_origin.port:
                raise OriginError(
                    "Port specified in Origin header is not allowed")

        if not (parsed_good_origin.hostname == parsed_request_origin.hostname
                and parsed_good_origin.scheme == parsed_request_origin.scheme):
            raise OriginError("Bad Origin header specified")

        return True

    @classmethod
    def _check_referer_ok(cls, request):
        """
        Checks if request Referer is good referer

        Returns:
            True if request referer is ok

        Raises:
            RefererError: If referer provided is invalid in any way
        """
        request_referer = request.referer

        if not request_referer:
            raise OriginError("No Referer header found in request")

        good_referer = "%s://%s:%d/" % (
            request.scheme,
            request.domain,
            request.port,
        )
        parsed_good_referer = urllib.parse.urlparse(good_referer)
        parsed_request_referer = urllib.parse.urlparse(request_referer)

        if parsed_request_referer.port:
            # there is port in referer header
            if parsed_request_referer.port != parsed_good_referer.port:
                raise RefererError(
                    "Port specified in Referer header is not allowed")

        if not (parsed_good_referer.hostname == parsed_request_referer.hostname
                and parsed_good_referer.scheme
                == parsed_request_referer.scheme):
            raise RefererError("Bad Referer header specified")

        return True

    @classmethod
    def check_csrf_cookie(cls, request):
        """
        Checks for the csrf cookie sent in request.

        Raises:
                CSRFCookieError: This is raised if there is any issue with the CSRF cookie sent by the client.
        """

        csrf_secret_from_cookie = request.META.get("CSRF_COOKIE")

        if not csrf_secret_from_cookie:
            cls.debug_message: str = "CSRFMiddleware: CSRF cookie not set"
            raise CSRFCookieError(
                "CSRF Cookie not set. This is required to ensure that your browser is not being hijacked by third parties"
            )

        if not len(csrf_secret_from_cookie) == CSRF_SECRET_LENGTH:
            cls.debug_message: str = (
                "CSRFMiddleware: CSRF cookie length invalid")
            raise CSRFCookieError("CSRF Cookie length invalid")

        if SETTINGS["CSRF_USE_SESSIONS"]:
            csrf_secret_from_session = request.SESSION.get(CSRF_SESSION_KEY)
            if (csrf_secret_from_session and
                    not csrf_secret_from_cookie == csrf_secret_from_session):
                cls.debug_message: str = "CSRFMiddleware: CSRF cookie mismatch"
                raise CSRFCookieError(
                    "CSRF Cookie mismatch. CSRF Cookie not matching csrf cookie from session"
                )

    @classmethod
    def get_error_response(cls, request):
        if SETTINGS["DEBUG"]:
            csrf_error_context = {"reason": "CSRFMiddleware error"}

            if hasattr(request, "csrf_error_reason"):
                csrf_error_context["reason"] = request.csrf_error_reason

            response = TemplateResponse(
                request,
                "csrf_error.html",
                context=csrf_error_context,
                content_type="text/html",
                status_code=403,
                engine=InternalDuckEngine.get_default(),
            )
        else:
            body = None
            response = make_simple_response(HttpForbiddenRequestResponse, body=body)
        return response

    @classmethod
    def process_response(cls, response, request):
        #[print(i, j) for i, j in request.META.items()]
        
        if request.META.get("CSRF_COOKIE_NEEDS_UPDATE"):
            # csrf cookie needs to be sent to client
            csrf_secret = request.META.get("CSRF_COOKIE")
            csrf_cookie_name = SETTINGS["CSRF_COOKIE_NAME"]
            csrf_cookie_domain = SETTINGS[
                "CSRF_COOKIE_DOMAIN"] or Meta.get_metadata(
                    "DUCK_SERVER_DOMAIN")
            max_age = SETTINGS["CSRF_COOKIE_AGE"]
            expires = datetime.datetime.utcnow() + datetime.timedelta(
                seconds=max_age)
            path = SETTINGS["CSRF_COOKIE_PATH"]
            secure = SETTINGS["CSRF_COOKIE_SECURE"]
            httponly = SETTINGS["CSRF_COOKIE_HTTPONLY"]
            samesite = SETTINGS["CSRF_COOKIE_SAMESITE"]
            
            if csrf_cookie_name in response.cookies:
                # Csrf cookie has been modified somehow, no need to set it.
                return
            
            if CSRF_USE_SESSIONS:
                # No need to send cookie, the csrf secret is available in user session
                return
            
            # Set csrf cookie
            response.set_cookie(
                csrf_cookie_name,
                value=csrf_secret,
                domain=csrf_cookie_domain,
                path=path,
                expires=expires,
                secure=secure,
                httponly=httponly,
                samesite=samesite,
            )

    @classmethod
    def is_duck_explicit_url(cls, url: str) -> bool:
        """
        Returns whether the request URL is in DUCK_EXPLICIT_URLS meaning,
        The request with the url doesn't need to be parsed to Django server first to produce a
        response, but rather to be handled by Duck directly.
        
        Notes:
            - This is only useful when USE_DJANGO=True as all requests all proxied to Django server to
            generate the http response.
        """
        # Duck explicit URLs are urls not to be proxied to Django even if USE_DJANGO=True.
        # They are handled directly by within Duck.
        duck_explicit_urls = SETTINGS["DUCK_EXPLICIT_URLS"] or []
        
        for duck_explicit_url in duck_explicit_urls:
            if re.compile(duck_explicit_url).fullmatch(url):
                # URL meant to be handle by Duck directly
                return True
        return False
    
    @classmethod
    def process_request(cls, request: HttpRequest):
        if SETTINGS["USE_DJANGO"] and not cls.is_duck_explicit_url(request.path):
            # This request is meant for Django to handle, no need to do Csrf middleware checks (Django will do it).
            return cls.request_ok
            
        csrf_token_name = "csrfmiddlewaretoken"
        csrf_session_key = CSRF_SESSION_KEY
        csrf_cookie_name = SETTINGS["CSRF_COOKIE_NAME"]
        csrf_header_name = SETTINGS["CSRF_HEADER_NAME"]
        csrf_secret_from_cookie = request.COOKIES.get(
            csrf_cookie_name) or request.get_header(csrf_header_name)

        if csrf_secret_from_cookie:
            request.META["CSRF_COOKIE"] = csrf_secret_from_cookie

        # Assume that anything not defined as 'safe' by RFC 9110 needs protection
        if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
            return cls.request_ok

        if SETTINGS["CSRF_USE_SESSIONS"]:
            correct_csrf_secret = request.SESSION.get(csrf_session_key)
        else:
            correct_csrf_secret = csrf_secret_from_cookie

        try:
            cls.check_csrf_cookie(request)
        except CSRFCookieError as e:
            request.csrf_error_reason = str(e)
            return cls.request_bad

        # perform origin and referer checks
        try:
            cls._check_origin_ok(request)
            cls._check_referer_ok(request)
        except Exception as e:
            if not isinstance(err, (OriginError, RefererError)):
                e = "Error in performing Origin and Referer header checks"
            request.csrf_error_reason = str(e)
            return cls.request_bad

        if not correct_csrf_secret:
            request.csrf_error_reason = (
                "Request might have expired, try reloading page")
            return cls.request_bad

        sent_token = request.QUERY["CONTENT_QUERY"].get(
            csrf_token_name, "") or request.get_header(csrf_header_name, "")
        try:
            sent_csrf_token_secret = (
                unmask_cipher_token(sent_token)
                or "<no-token>")
        except:
            sent_csrf_token_secret = "<invalid-token>"

        if not (constant_time_compare(sent_csrf_token_secret, correct_csrf_secret)
            and len(correct_csrf_secret) == CSRF_SECRET_LENGTH
            and len(sent_csrf_token_secret) == CSRF_SECRET_LENGTH):
            request.csrf_error_reason = (
                "CSRF token missing or invalid, try reloading page")
            return cls.request_bad

        # Warning: don't rotate csrf_token yet as this might mean user needs to reload web form every time.
        return cls.request_ok
