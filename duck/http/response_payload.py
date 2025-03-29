"""
Module representing response payload classes.
"""
import importlib

from datetime import timedelta, datetime
from typing import Optional, Dict, Any, Union

from duck.etc.statuscodes import responses
from duck.http.headers import Headers
from duck.utils.object_mapping import map_data_to_object


# Dynamically load the standard library module `http.cookies`
# This is done to avoid using the duck.http module.
cookies_module = importlib.import_module("http.cookies")


# Use the module as usual
SimpleCookie = cookies_module.SimpleCookie


class BaseResponsePayload:
    """
    BaseResponsePayload class.
    """
    @property
    def raw(self):
        raise NotImplementedError("Property `raw` should be implemented.")
    
    @property
    def cookies(self) -> SimpleCookie:
        """
        Property getter for cookies. If not already initialized, it initializes the cookies.
        
        Returns:
            SimpleCookie: The cookies for the response.
        """
        if not hasattr(self, '_cookies'):
            self._cookies = SimpleCookie()  # Initialize cookies if not already set
        return self._cookies

    @cookies.setter
    def cookies(self, cookies_obj: SimpleCookie) -> None:
        """
        Setter for cookies. Assigns a SimpleCookie object to the internal cookies attribute.
        
        Args:
            cookies_obj (SimpleCookie): The SimpleCookie object to set.
        """
        
        if not isinstance(cookies_obj, SimpleCookie):
            raise ValueError("Expected a SimpleCookie object.")
        self._cookies = cookies_obj

    def set_multiple_cookies(self, cookies: Dict[str, Dict[str, Any]]) -> None:
        """
        Sets multiple cookies at once. Each cookie is specified by a dictionary of attributes.
        
        Args:
            cookies (Dict[str, Dict[str, Any]]): A dictionary where the key is the cookie name
                                                 and the value is another dictionary of cookie attributes.
        """
        for cookie_name, attributes in cookies.items():
            self.set_cookie(cookie_name, **attributes)

    def get_cookie(self, name: str) -> str:
        """
        Retrieves the value of a specific cookie by name.
        
        Args:
            name (str): The name of the cookie to retrieve.
        
        Returns:
            str: The cookie value, or an empty string if the cookie does not exist.
        """
        return self._cookies.get(name, '').value if name in self._cookies else ''

    def get_all_cookies(self) -> Dict[str, str]:
        """
        Retrieves all cookies as a dictionary.
        
        Returns:
            Dict[str, str]: A dictionary of all cookies, where the key is the cookie name and the value is the cookie value (without other cookie properties).
        """
        return {key: morsel.value for key, morsel in self._cookies.items()}
    
    def set_cookie(
        self,
        key: str,
        value: str = "",
        domain: Optional[str] = None,
        path: str = "/",
        max_age: Optional[Union[int, timedelta]] = None,
        expires: Optional[Union[datetime, str]] = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: Optional[str] = "Lax",
    ) -> None:
        """
        Set a custom cookie on the response payload.
    
        Args:
            key (str): The name of the cookie (e.g., 'csrftoken').
            value (str): The value of the cookie (e.g., 'some_random_token').
            domain (Optional[str]): The domain to set for the cookie. Defaults to None.
            path (str): The path for the cookie. Defaults to '/' indicating the whole site.
            max_age (Optional[Union[int, timedelta]]): The maximum age of the cookie in seconds or as a timedelta object.
            expires (Optional[Union[datetime, str]]): The expiration date of the cookie. Defaults to None.
            secure (bool): Whether the cookie should only be sent over HTTPS connections. Defaults to False.
            httponly (bool): Whether the cookie should be inaccessible to JavaScript. Defaults to False.
            samesite (Optional[str]): The SameSite attribute for the cookie. Default is 'Lax'. Other possible values are 'Strict' or 'None'.
    
        Raises:
            ValueError: If an invalid value is provided for `samesite`.
        """
        # Validate SameSite value
        valid_samesite_values = {"Lax", "Strict", "None", None}
        if samesite is not None:
            samesite = str(samesite).capitalize()  # Normalize capitalization
            if samesite not in valid_samesite_values:
                raise ValueError(f"Invalid 'samesite' value: {samesite}. Must be one of {valid_samesite_values}.")
        
        # Set the cookie
        self.cookies[key] = value
        cookie = self.cookies[key]
    
        # Optional attributes
        if domain:
            cookie["domain"] = domain
        cookie["path"] = path
        if max_age is not None:
            # Convert timedelta to seconds if necessary
            max_age_seconds = max_age.total_seconds() if isinstance(max_age, timedelta) else max_age
            cookie["max-age"] = int(max_age_seconds)
            # Calculate expires if not explicitly provided
            if expires is None:
                expires = datetime.utcnow() + timedelta(seconds=max_age_seconds)
        if expires is not None:
            if isinstance(expires, datetime):
                expires = expires.strftime('%a, %d %b %Y %H:%M:%S GMT')
            cookie["expires"] = expires
        if secure:
            cookie["secure"] = True
        if httponly:
            cookie["httponly"] = True
        if samesite:
            cookie["samesite"] = samesite
    
    def delete_cookie(self, key: str, path: str = "/", domain: Optional[str] = None) -> None:
        """
        Delete a cookie from the response payload by setting its expiration date to the past.
        This will prompt the client to remove the cookie.

        Args:
            key (str): The name of the cookie to delete.
            path (str): The path for which the cookie was set. Defaults to "/".
            domain (Optional[str]): The domain for which the cookie was set. Defaults to None.
        """
        cookie = self.cookies[key] = ""
        cookie["path"] = path
        cookie["domain"] = domain or ""
        cookie["expires"] = datetime.utcfromtimestamp(0).strftime('%a, %d %b %Y %H:%M:%S GMT') # unix epoch
        cookie["max-age"] = 0
        cookie["secure"] = False
        cookie["httponly"] = False
        cookie["samesite"] = "Lax"


class SimpleHttpResponsePayload(BaseResponsePayload):
    """
    A class representing a simplified HTTP response payload, storing basic response metadata such as the
    top header (status line) and HTTP headers.

    This class is used for lightweight storage and manipulation of HTTP response headers and status-related
    information. It does not handle the response body.

    Attributes:
        cookies: The http.cookies.SimpleCookie object for all cookies.
        topheader (str): The status line of the HTTP response (e.g., "200 OK"). Defaults to an empty string.
        headers (Headers): A `Headers` object containing the HTTP response headers. Defaults to `None`.

    Methods:
    - set_topheader(topheader: str):
          Updates the top header (status line) of the response.

    - set_headers(headers: dict):
        Updates the HTTP headers using a dictionary input.

    Properties:
    - status_code (int):
        Extracts and returns the status code from the `topheader`.

    - status_message (str):
        Extracts and returns the status message from the `topheader`. Defaults to an empty string if the 
            `topheader` is not set.

    - explanation (str):
          A placeholder for additional explanation or description of the status. Currently always returns an 
            empty string.
    """

    def __init__(self, topheader: str = "", headers: Optional[Dict] = None):
        """
        Initializes a SimpleHttpResponsePayload instance.

        Args:
            topheader (str): The HTTP response status line (e.g., "200 OK"). Defaults to an empty string.
            headers (Optional[Dict]): A dictionary representing the HTTP response headers. Defaults to `None`.
        """
        if not topheader or not isinstance(topheader, str):
            raise ValueError("The 'topheader' argument must be a non-empty string.")
        self.topheader = topheader
        self.headers = Headers(headers or {})

    @property
    def raw(self) -> bytes:
        """
        Constructs and returns the raw HTTP response as bytes.
    
        This property generates a raw representation of the HTTP response by combining the `topheader` (status line)
        and all headers stored in the `headers` attribute. Each header is formatted as "Header-Name: value", separated
        by carriage return and newline characters (`\r\n`). The resulting raw response is encoded as UTF-8.
    
        Returns:
            bytes: The raw HTTP response as bytes.
        """
        data = f"{self.topheader}"
        for header, value in self.headers.titled_headers().items():
            data += f"\r\n{header}: {value}"
        cookies = self.cookies.output()
        data += "\r\n" + cookies
        return data.encode("utf-8").strip()
        
    def set_topheader(self, topheader: str):
        """
        Updates the status line of the HTTP response.

        Args:
            topheader (str): The new HTTP status line (e.g., "404 Not Found").
        """
        if topheader:
            self.topheader = topheader

    def set_header(self, header: str, value: str):
        """
        Sets header and value for the payload
        """
        self.headers[header] = value

    def get_header(self, header: str, default_value=None) -> Optional[str]:
        """
        Returns a header value of default if not found.
        """
        return self.headers.get(header, default_value)

    @property
    def status_code(self) -> int:
        """
        Extracts and returns the HTTP status code from the status line.

        Returns:
            int: The HTTP status code (e.g., 200).
        
        """
        return int(self.topheader.split(" ", 2)[1])

    @property
    def status_message(self) -> str:
        """
        Extracts and returns the HTTP status message from the status line.

        Returns:
            str: The HTTP status message (e.g., "OK").
        """
        return self.topheader.split(" ", 2)[-1]

    @property
    def explanation(self) -> str:
        """
        Placeholder for additional status explanation.

        Returns:
            str: Always returns an empty string.
        """
        return ""
    
    @property
    def http_version(self) -> str:
        """
        Extracts and returns the HTTP version from the `topheader`.
    
        This property analyzes the `topheader` (status line) of the HTTP response and retrieves the HTTP version,
        such as "HTTP/1.1" or "HTTP/2". If the `topheader` is not set or improperly formatted, it defaults to the
        last version in `HttpRequest.SUPPORTED_HTTP_VERSIONS`.
    
        Returns:
            str: The HTTP version extracted from the `topheader` or the default version if unavailable.
        """
        from duck.http.request import HttpRequest
        
        if self.topheader:
            return self.topheader.split(" ", 1)[0]
        return HttpRequest.SUPPORTED_HTTP_VERSIONS[-1]  # Default to the latest supported HTTP version.
    
    def __repr__(self):
        return f'<{self.__class__.__name__} "{self.topheader}">'


class HttpResponsePayload(BaseResponsePayload):
    """
    ResponsePayload class for storing response top header and headers.

    Example payload:
    
    ```
    200 OK\r\n
    Connection: close\r\n
    Content-Type: text/html\r\n
    ```
    """

    def __init__(self, **kwargs):
        """
        Args:
            status_code (int): The status code for the response. Default value is 200.
            status_message (str): The status message corresponding to the status code.
            headers (Headers): The headers to attach to the response payload.
            http_version (str): The HTTP version for the server. Default value is 'HTTP/2.1'
            explanation (str): A longer explanation of the status message.
        """
        from duck.http.request import HttpRequest

        self.status_code: int = 200
        self.status_message: str = ""
        self.headers: Headers = Headers()
        self.http_version: str = HttpRequest.SUPPORTED_HTTP_VERSIONS[-1]
        self.explanation: str = ""

        # map kwargs to self
        map_data_to_object(self, kwargs)

    @property
    def raw(self) -> bytes:
        """Returns the raw bytes representing the payload"""
        topheader = "%s %d %s" % (
            self.http_version,
            self.status_code,
            self.status_message,
        )
        data = f"{topheader}"
        for header, value in self.headers.titled_headers().items():
            data += f"\r\n{header}: {value}"
        cookies = self.cookies.output()
        data += "\r\n" + cookies
        return data.encode("utf-8").strip()
        
    def set_header(self, header: str, value: str):
        """
        Sets header and value for the payload
        """
        self.headers[header] = value

    def get_header(self, header: str, default_value=None) -> Optional[str]:
        """
        Returns a header value of default if not found.
        """
        return self.headers.get(header, default_value)

    def parse_status(
        self,
        code: int,
        msg: str = None,
        explanation: str = None):
        """
        Parses topheader status for the payload.
        """
        if code in responses:
            # status code exists
            short_msg, long_msg = responses[code]
            if not msg:
                msg = short_msg
            if not explanation:
                explanation = long_msg
        else:
            if not msg:
                msg = "???"
            if not explanation:
                if msg != "???":
                    explanation = msg
                else:
                    explanation = "???"
        self.status_message = msg
        self.status_code = code
        self.explanation = explanation
        
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.status_code}>"
