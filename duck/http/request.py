"""
Module containing Request class which represents an http request.

``` {note}
If you run into errors or unexpected behavior when interacting with a request, be sure to inspect the `Request.error` attribute for diagnostic information.
```

"""
import json
import socket
import hashlib
import random

from typing import Dict, Optional, Tuple
from urllib.parse import parse_qs

from duck.exceptions.all import (
    RequestError,
    RequestHostError,
    RequestSyntaxError,
    RequestUnsupportedVersionError,
)
from duck.meta import Meta
from duck.settings import SETTINGS
from duck.http.content import Content
from duck.http.fileuploads.multipart import BytesMultiPartParser
from duck.http.headers import Headers
from duck.http.querydict import FixedQueryDict, QueryDict
from duck.http.request_data import RequestData, RawRequestData
from duck.utils.importer import import_module_once
from duck.utils.object_mapping import map_data_to_object
from duck.utils.urldecode import url_decode
from duck.utils.urlcrack import URL
from duck.utils.path import build_absolute_uri


SUPPORTED_HTTP_VERSIONS = ["HTTP/1.0", "HTTP/1.1"]


class Request:
    """
    An object representing an HTTP request, including method, headers, and body data.
    
    Notes:
    - If you run into errors or unexpected behavior when interacting with a request, be sure to inspect the `Request.error` attribute for diagnostic information.
    - The recommended method for parsing raw request data is to use `parse`.
    """
    
    SUPPORTED_HTTP_VERSIONS: list = SUPPORTED_HTTP_VERSIONS
    """
    List of all supported http versions e.g `HTTP/1.1`.
    
    ``` {important}
    This is case-sensitive, only caps are allowed.
    ```
    """

    def __init__(self, **kwargs):
        """
        Initializes a request object, populating fields based on available data.

        Args:
            method (str): The HTTP method (e.g., 'GET', 'POST', 'PUT', 'DELETE').
            path (str): The request path (excluding domain and query string).
            http_version (str): The HTTP version (e.g., 'HTTP/1.1', 'HTTP/2').
            headers (Headers): Request headers in lowercase key-value pairs.
            error (Exception): An optional exception raised during parsing.
            protocol (str): The protocol used (typically 'HTTP').
            content_obj (Content): Optional content object.
            
        Notes:
            - To extract information like request port, the 'Host' header must be present.
            - This class aims to encapsulate request details for further processing.
            - Use method 'parse_raw_request' to populate request using raw data.
            - The application attribute will be set by WSGI creating request
            - The SESSION attribute is an instance of SessionStore
            - The QUERY attribute is an instance of QueryDict which contains 'CONTENT_QUERY' and 'URL_QUERY'
            - These two keys contains both content queries and url queries respectively
        """
        from duck.settings.loaded import SESSION_STORE
        
        # The `request_store` is a dictionary originating from the RequestData object.
        # It allows you to attach custom metadata to the request during early parsing,
        # and access or modify that data later in the request lifecycle (e.g., middleware, views).
        # This is useful for carrying values derived during initial request handling without
        # modifying core request attributes.
        # 
        # Example:
        # request_data = RequestData(headers={"topheader": "GET / HTTP/1.1"}, data=b'')
        # request_data.request_store["something"] = "anything"
        # request = Request()
        # request.parse(request_data)
        # print(request.request_store["something"]) # Outputs 'anything'
        
        self.__meta = {}  # meta for the request
        self.__session = SESSION_STORE(None)  # session for the request
        self.__remote_addr: tuple[str, int] = None  # client remote address and port
        self.__headers: Headers = Headers()  # request headers
        self.__fullpath: str = None  # full path for the request
        self.__path: str = None  # path stripped of queries if so
        self.__id: str = None  # request unique identifier
        
        self.client_socket: socket.socket = None # client socket which made this request
        self.application = None
        self.method: str = ""
        self.path: str = ""
        self.http_version: str = ""
        self.error: Exception = None
        self.request_store = {}
        self.content_obj: Content = Content(b"", suppress_errors=True)
        self.topheader: str = ""  # topheader .e.g GET / HTTP/1.1
        self.request_data: RequestData = None # Will be set when Request.parse is used
        self.uses_ipv6 = Meta.get_metadata("DUCK_USES_IPV6")
        
        self.AUTH: dict = dict()
        self.META: dict = self.__meta
        self.FILES: dict = dict()
        self.COOKIES: dict = dict()
        self.GET: QueryDict = QueryDict()
        self.POST: QueryDict = QueryDict()
        self.QUERY: FixedQueryDict[str, QueryDict] = FixedQueryDict({
            "CONTENT_QUERY": QueryDict(),
            "URL_QUERY": QueryDict(),
        })
        
        if kwargs.get("content_obj", None) and kwargs.get("content", None):
            raise RequestError(
                "Please provide one of these arguments ['content', 'content_obj'] not both"
            )
        
        # Setting all key, value pairs in kwargs as attributes and attribute values
        map_data_to_object(self, kwargs)
        
        if kwargs.get("content", None):
            self.set_content(kwargs.get("content"))

    @property
    def ID(self):
        """
        Retrieves the 8-bit unique identifier for the request.
    
        If the ID has not been generated yet, it will be created using a hash of a random number.
        The ID is represented as a substring of the MD5 hash, limited to the first 8 characters.
    
        Returns:
            str: The 8-character unique identifier for the request.
        """
        if not self.__id:
            self.__id = hashlib.md5(str(random.random()).encode("utf-8")).hexdigest()[:8]
        return self.__id
    
    @property
    def content(self):
        """
        Retrieves the content data associated with the request.
    
        Returns:
            Any: The data of the content associated with the request, typically the payload.
        """
        return self.content_obj.data
    
    @property
    def json(self):
        """
        Retrieves the json from the request content.

        Returns:
            dict: The data of the content associated with the request, typically the payload.
        
        Raises:
            ValueError: If the request body cannot be parsed as JSON.
        """
        try:
            # Load the JSON content from the request body
            return json.loads(self.content.decode('utf-8'))
        except json.JSONDecodeError as e:
            raise ValueError("Invalid JSON data in the request") from e
    
    @property
    def protocol(self) -> Optional[str]:
        """
        Retrieves the HTTP version used in the request.
    
        This returns the protocol version specified in the request, typically 
        in the format of 'HTTP/1.1' or 'HTTP/2'. If the protocol is not defined, 
        it returns None.
    
        Returns:
            Optional[str]: The HTTP protocol version, or None if not set.
        """
        return self.http_version
    
    @property
    def path(self) -> Optional[str]:
        """
        Retrieves the path portion of the request URL.
    
        This property returns the URL path without any query parameters, 
        representing the main part of the request URL.
    
        Returns:
            Optional[str]: The path of the request, or `None` if not set.
        """
        return self.__path
    
    @path.setter
    def path(self, path: Optional[str]):
        """
        Sets the path portion of the request URL.
    
        If a valid path is provided, it will be stored as the URL path. If the path contains
        query parameters (indicated by a `?`), it will update the `fullpath` to include the query part as well.
        If the path is empty or falsy, it will set the path to `None`.
    
        Args:
            path (Optional[str]): The path to set for the request, which may optionally contain query parameters.
    
        Notes:
            - If the `path` contains a query string (e.g., `/home?q=12`), only the path part (`/home`) is stored,
              and `fullpath` is updated accordingly.
            - If `path` is falsy (empty or `None`), the path is cleared.
        """
        if not path:
            self.__path = path
            return
        if "?" in path:
            self.fullpath = path
        self.__path = path.split("?")[0]
    
    @property
    def fullpath(self):
        """
        Retrieves the full path of the request, including query parameters.
    
        This includes both the path and any query strings, for example: 
        `/home?q=12&w=4`.
    
        Returns:
            str: The full path of the request.
        """
        return self.__fullpath

    @fullpath.setter
    def fullpath(self, path: str):
        """
        Sets the full URL path for the request, including any query parameters.
    
        This setter updates both the `fullpath` and `path` attributes. The `fullpath` 
        includes the entire URL path, while the `path` stores only the portion before
        any query parameters (i.e., the main path).
    
        If the provided `path` is empty or falsy, both `fullpath` and `path` will be cleared.
    
        Args:
            path (str): The full URL path to set, which may include query parameters.
    
        Notes:
            - If the `path` contains a query string (e.g., `/home?q=12`), the `fullpath` will store the full path,
              and `path` will store only the portion before the `?` (i.e., `/home`).
            - If the `path` is falsy (empty or `None`), both `fullpath` and `path` are cleared.
        """
        self.__fullpath = path
        if not path:
            self.__path = path
            return
        self.__path = path.split("?")[0]

    @property
    def SESSION(self):
        """
        Retrieves the session associated with the request.
    
        This property returns the internal session object, which is typically used 
        for tracking and managing the state of a user's session throughout the 
        lifecycle of a request.
    
        Returns:
            Any: The session object associated with the request.
        """
        return self.__session
    
    @property
    def session(self):
        """
        Alias for the `SESSION` property.
    
        This provides the same value as `request.SESSION`, allowing an alternative 
        way to access the session object.
    
        Returns:
            Any: The session object associated with the request.
        """
        return self.SESSION
    
    @SESSION.setter
    def SESSION(self, session):
        """
        Sets the session for the request.
    
        This setter associates the provided session with the request. Additionally,
        it sets the request as an attribute of the session, enabling reverse access 
        from the session back to the request.
    
        Args:
            session (Any): The session object to associate with the request.
    
        Notes:
            - The session's `request` attribute will be set to the current request instance.
        """
        self.__session = session
        self.__session.request = self
    
    @property
    def headers(self) -> dict:
        """
        Retrieves the headers of the request.
    
        This property returns the request headers as a dictionary with all header 
        names in lowercase.
    
        Returns:
            dict: The headers of the request, represented as a dictionary where 
            all header names are in lowercase.
        """
        return self.__headers
    
    @headers.setter
    def headers(self, headers):
        """
        Sets the headers for the request.
    
        This setter updates the request's headers. It expects the provided headers 
        to be an instance of the `Headers` class. If the headers are not of the 
        correct type, a `RequestError` will be raised.
    
        Args:
            headers (Headers): The headers to set for the request.
    
        Raises:
            RequestError: If the provided `headers` is not an instance of the `Headers` class.
    
        Notes:
            - If the headers are valid, they will be updated in the request's `headers` attribute.
        """
        if not isinstance(headers, Headers):
            raise RequestError(
                f"Request headers should be an instance of 'duck.http.header.Headers', not {type(headers)}"
            )
        self.headers.update(headers)
    
    @property
    def title_headers(self) -> dict:
        """
        Request headers in title format rather than small cased
        e.g. {'Connection': 'close'} rather than {'connection': 'close'}
        """
        return self.headers.titled_headers()

    @property
    def uses_https(self):
        """Whether the request is on `HTTP` or `HTTPS` protocol, this is determined by checking if application is started with https enabled or not"""
        if self.application:
            if self.application.enable_https:
                return True
        else:
            return True if SETTINGS["ENABLE_HTTPS"] else False
        return False
    
    @property
    def hostname(self) -> str:
        """
        Returns the hostname within the Host header.
        """
        return URL(self.host).host
    
    @property
    def port(self) -> Optional[int]:
        """
        Returns the port as integer within the Host header.
        
        Returns:
            Optional[int]: If port exists within the Host header else None
        """
        return URL(self.host).port
        
    @property
    def host(self) -> str:
       """
        Returns the value of the Host header in the request.
    
        If the Host header is not set, raises a RequestHostError.
    
        Returns:
            str: The value of the Host header.
    
        Raises:
            RequestHostError: If the Host header is not set in the request.
        """
       host = self.get_header("host", None)
       if not host:
           raise RequestHostError("Host header not set in request.")
       return host

    @property
    def origin(self) -> Optional[str]:
        """
        Retrieves the 'Origin' header from the HTTP request.
    
        The 'Origin' header indicates the origin (protocol, host, and port) of the request.
        It is typically used in cross-origin requests to specify the origin making the request.
    
        Returns:
            Optional[str]: The value of the 'Origin' header, or None if the header is not set.
        """
        return self.get_header("origin")

    @property
    def referer(self) -> Optional[str]:
        """
        Retrieves the 'Referer' header from the HTTP request.
    
        The 'Referer' header indicates the address of the previous web page from which a link to the currently requested page was followed. 
    
        Returns:
            Optional[str]: The value of the 'Referer' header, or None if the header is not set.
        """
        return self.get_header("referer")
    
    @property
    def scheme(self) -> str:
        """
        Retrieves the scheme (protocol) of the HTTP request.
    
        The scheme is typically 'http' or 'https', indicating the protocol used for the request.
        This method returns 'https' if the request uses HTTPS, otherwise it returns 'http'.
    
        Returns:
            str: The scheme (either 'http' or 'https') for the request.
        """
        if self.uses_https:
            return "https"
        return "http"
        
    @property
    def version_number(self) -> Optional[str]:
        """
        Get the version number of the request as a string.

         Notes:
                This is very different from attr `http_version` as it only includes version number as a string
        """
        if not self.http_version:
            return
        return self.http_version.split("/")[-1].strip()

    @property
    def has_error(self) -> bool:
        """Returns boolean on whether boolean has an error."""
        return bool(self.error)

    @property
    def connection(self) -> str:
        """
        Retrieves the connection mode for the request.
    
        This property returns the value of the `Connection` header from the request, 
        or defaults to `'close'` if the header is not set.
    
        Returns:
            str: The connection mode for the request. Defaults to `'close'` if not set.
    
        Notes:
            - The `Connection` header controls whether the network connection 
              should be kept alive or closed after the request is completed.
        """
        return self.get_header("connection", "close")
    
    @property
    def absolute_uri(self) -> str:
        """
        Resolves the absolute URI for the current request.
    
        This property constructs the absolute URI by combining the base URL and 
        the request path. The absolute URI includes the full protocol, domain, 
        and path to the requested resource.
    
        Returns:
            str: The absolute URI of the request, including scheme and domain.
        """
        root_url = URL(self.host)
        root_url.scheme = self.scheme
        root_url = root_url.to_str()
        return build_absolute_uri(root_url, self.path)

    @property
    def META(self) -> dict:
        """
        Retrieves the metadata associated with the request.
    
        This property calls the `build_meta` method to ensure the request's metadata 
        is up-to-date and then returns the stored metadata dictionary.
    
        Returns:
            dict: A dictionary containing the metadata of the request.
    
        Notes:
        - The `build_meta` method is called each time this property is accessed 
              to ensure the metadata is fresh.
        """
        self.build_meta()
        return self.__meta
    
    @META.setter
    def META(self, meta: dict):
        """
        Updates the request's metadata.
    
        This setter updates the stored metadata dictionary with new values. The 
        provided `meta` dictionary will be merged with the existing metadata.
    
        Args:
            meta (dict): A dictionary containing metadata to update the request's 
            metadata.
    
        Notes:
            - The provided `meta` dictionary is merged with the existing metadata 
              using the `update` method.
        """
        self.__meta.update(meta)
    
    @property
    def raw(self) -> bytes:
        """
        Construct raw request from this `Request` object.
        """
        # Add Authorization headers if not already set
        self._set_auth_headers()
        
        # Start constructing the request with the method, path, and HTTP version
        request = self._build_request_line()
        
        # Add headers to the request
        request += self._build_headers()
        request = request.strip()
        
        # Append the content if it exists
        if self.content:
            request += b"\r\n\r\n" + self.content
        return request
    
    @staticmethod
    def extract_cookies_from_request(request) -> Dict[str, str]:
        """
        Extracts and returns the cookies from the given request.
    
        This static method extracts cookies from the request object and returns them 
        as a dictionary, where each key is a cookie name and the corresponding value 
        is the cookie's value.
    
        Args:
            request (Request): The request object from which to extract cookies.
    
        Returns:
            Dict[str, str]: A dictionary containing the cookies extracted from the 
            request, with cookie names as keys and cookie values as values.
    
        Notes:
            - The request must have a way of storing cookies (e.g., in a `cookies` 
              attribute or method).
        """
        cookies_header = request.get_header("Cookie", "")
        cookies = {}
        
        if not cookies_header:
            return {}
        
        for cookie in cookies_header.split(";"):
            if "=" in cookie:
                key, value = map(str.strip, cookie.split("=", 1))
                cookies[key] = value
        return cookies

    @staticmethod
    def extract_auth_from_request(request) -> Dict[str, str]:
        """Extracts authentication-related information from the request headers.
    
        This method looks for both the `Authorization` and `Proxy-Authorization` headers and
        returns a dictionary containing the values if they exist.
    
        Args:
            request: The request object containing the headers to extract from.
    
        Returns:
            Dict[str, str]: A dictionary with keys 'auth' and 'proxy_auth', containing
                            the corresponding header values if present. If neither header
                            is found, an empty dictionary is returned.
    
        Example:
        
        ```py
        request = SomeRequestObject()
        auth_data = extract_auth_from_request(request)
        print(auth_data)  # Outputs {'auth': 'Bearer token_value', 'proxy_auth': 'Basic proxy_token'}
        ```
        """
        # Initialize the dictionary to hold the extracted authentication data
        data: Dict[str, str] = {}
    
        # Retrieve the Authorization and Proxy-Authorization headers
        auth = request.get_header("Authorization", None)
        proxy_auth = request.get_header("Proxy-Authorization", None)
    
        # If the Authorization header is found, add it to the data dictionary
        if auth:
            data["auth"] = auth.strip()
    
        # If the Proxy-Authorization header is found, add it to the data dictionary
        if proxy_auth:
            data["proxy_auth"] = proxy_auth.strip()
    
        # Return the extracted data (which may be empty if no relevant headers were found)
        return data

    @staticmethod
    def extract_content_queries(request) -> QueryDict:
        """
         Extract query parameters and file uploads from the request content.
    
         This method retrieves all query parameters from the request body,
         including files and form data. However, uploaded files are not
         automatically saved—you must manually call `save()` on
         `request.FILES[query_key]` where necessary.
    
         Args:
            request (HttpRequest): The incoming HTTP request object.
    
         Returns:
            QueryDict: A dictionary-like object containing extracted query parameters
                       and file data from the request.
        """
        from duck.settings.loaded import FILE_UPLOAD_HANDLER

        content_type = request.get_header("content-type", "").strip()

        if content_type.lower().startswith("application/json"):
            try:
                return QueryDict(json.loads(request.content.decode("utf-8")))
            except json.JSONDecodeError and ValueError:
                # except json.JSONDecodeError, ValueError or any other error
                pass

        elif content_type.lower().startswith(
                "application/x-www-form-urlencoded"):
            try:
                post = QueryDict()
                [
                    post.update({key: val[0]}) for key, val in parse_qs(
                        request.content.decode("utf-8")).items()
                ]
                return post
            except Exception:
                pass

        elif content_type.lower().startswith("multipart/"):
            headers = {"Content-Type": content_type}
            input_data = request.content
            parser = BytesMultiPartParser(headers, input_data)
            queries = QueryDict()

            for headers, content in parser.get_parts():
                # get content disposition from headers
                content_disposition = headers.get("Content-Disposition")
                data = content_disposition.split(
                    ";"
                )[1:]  # skip first data value as it indicate the content-disposition e.g. form-data
                dictdata = {}
                for i in data:
                    if not i:
                        continue
                    if "=" in i:
                        key, value = i.split("=")
                    else:
                        key, value = i, ""
                    key, value = key.strip().replace("'", "").replace(
                        '"', ""), value.strip().replace("'",
                                                        "").replace('"', "")
                    dictdata[key] = value

                # dictdata is in form
                # {'name': 'field1'} or
                # {'name': 'field1', 'filename': 'filename'}
                query_content = content
                query_key = dictdata["name"]

                if "filename" in dictdata:
                    # this is a file, skip adding it queries but to request.FILES instead
                    # with key dictdata.name
                    filename = dictdata["filename"]

                    if not filename:
                        # no file has been selected or attached in html form, skip
                        continue

                    # create an uploadedfile object
                    additional_kw = {
                        "name": query_key,
                        "content_type": headers.get("Content-Type"),
                        "content_disposition": content_disposition,
                    }

                    file_upload_handler = FILE_UPLOAD_HANDLER(
                        filename, content, **additional_kw)

                    # Add file in request.FILES
                    request.FILES[query_key] = file_upload_handler
                    
                    # Skip to next content disposition
                    continue

                # record some data
                queries[query_key] = query_content.decode("utf-8")
            return queries
        return QueryDict()
        
    @staticmethod
    def extract_url_queries(url: str) -> Tuple[str, QueryDict]:
        """
        Extracts the query parameters from a given URL.
    
        This method splits the provided URL into two parts:
            - The base URL (without the query string).
            - A `QueryDict` containing the parsed query parameters.
    
        Args:
            url (str): The URL containing the query string (e.g., `/path/?query1=value1&query2=value2`).
    
        Returns:
            Tuple[str, QueryDict]: A tuple where the first element is the base URL 
            (without the query string) and the second element is a `QueryDict` 
            containing the query parameters.
    
        Notes:
            - The `QueryDict` object is a specialized dictionary that can handle multiple 
              values for the same query key.
            - If the URL does not contain query parameters, the second element of the 
              returned tuple will be an empty `QueryDict`.
    
        Example:
            url = "/path/?query1=value1&query2=value2"
            base_url, queries = extract_url_queries(url)
            print(base_url)  # "/path/"
            print(queries)   # {"query1": ["value1"], "query2": ["value2"]}
        """
        splits = url.split("?", 1)
        _queries = QueryDict()
    
        if len(splits) == 1:
            # No queries present
            return url, _queries
    
        # The URL part before the "?" and the queries after
        url, queries = splits
        for query in queries.split("&"):
            key_value = query.split("=", 1)
    
            if len(key_value) == 1:
                # Key is present but no value (e.g., "key=")
                _queries[key_value[0].strip()] = []
            else:
                key, value = key_value
                key = key.strip()
                value = value.strip()
                # Appending values to the key in QueryDict
                _queries.appendlist(key, value)
        return url, _queries

    @staticmethod
    def add_queries_to_url(url: str, queries: Dict) -> str:
        """This adds queries to a URL"""
        if not isinstance(queries, dict):
            raise RequestError(
                f"Argument `queries` should be a dict not {type(queries)}")
        url = (url.strip("?") + "?" if queries else url.strip("?"))  # remove existing if so and add new (?)
        counter = 0
        for key in queries.keys():
            url += "&" if counter >= 1 else ""
            url += f"{key}=" + "%s" % queries.get(key)
            counter += 1
        return url
        
    @property
    def remote_addr(self) -> Tuple[str, int]:
        """Returns the client remote address and port"""
        if self.__remote_addr:
            return self.__remote_addr

        if self.client_socket:
            try:
                self.__remote_addr = self.client_socket.getsockname()
            except socket.error:
                pass
        return self.__remote_addr
    
    def build_meta(self) -> Dict:
        """
        Builds and returns the metadata associated with the request.
    
        This method collects relevant information about the current request and 
        compiles it into a dictionary. The metadata can include details such as 
        headers, request method, URI, and other contextual data that may be useful 
        for logging, debugging, or request processing.
    
        Returns:
            Dict: A dictionary containing metadata about the request.
    
        Notes:
            - The specific metadata included in the dictionary depends on the 
              implementation and purpose of the request.
        """
        q = self.fullpath.split("?", 1) if self.fullpath else ""
        meta = Meta.compile()
        server_name = meta.get("DUCK_SERVER_NAME")
        server_port = meta.get("DUCK_SERVER_PORT")
        request_method = self.method or ""
        query_string = q[-1] if len(q) > 1 else ""
        remote_addr = self.remote_addr

        # only put essential meta
        self.__meta.update({
            "SERVER_NAME": server_name,
            "SERVER_PORT": server_port,
            "SERVER_PROTOCOL": self.protocol or "",
            "REQUEST_METHOD": request_method or "",
            "PATH_INFO": self.path or "",
            "QUERY_STRING": query_string,
        })

        # Add remote addr to meta
        if remote_addr:
            self.__meta.update({
                "REMOTE_ADDR": remote_addr[0],
                "REMOTE_PORT": remote_addr[1]
            })

        # Add headers in META
        for h in self.headers:
            if h.startswith("content"):
                self.__meta[h.upper()] = self.headers[h]
            else:
                self.__meta["HTTP_" + h.upper()] = self.headers[h]
        self.__meta.update(meta)
        return self.__meta

    def build_absolute_uri(self, path: str = None) -> str:
        """
        Constructs an absolute URL by combining the scheme, netloc, and the provided path.
    
        This method ensures that the resulting URL includes the scheme, host, and port (if applicable).
        It relies on the `scheme` and `port` attributes for accurate URL construction.
    
        Args:
            path (str, optional): The URL path to append to the base URL. Defaults to None.
    
        Returns:
            str: A fully constructed absolute URL.
        """
        if not path:
            return self.absolute_uri
        return build_absolute_uri(self.absolute_uri, path)
    
    def set_connection(self, mode: str):
        """Sets the request connection mode by modifying the connection header."""
        if mode.lower() not in ["close", "keep-alive"]:
            raise RequestError(
                "Connection mode can only be between 'close' and 'keep-alive' "
            )
        self.set_header("Connection", mode)

    def set_header(self, header: str, value: str):
        """
        Adds or replaces a header in the request.
    
        This method ensures that all header names are stored in lowercase within `self.headers`
        for consistency and proper handling of headers, as HTTP header names are case-insensitive.
    
        Args:
            header (str): The name of the header to add or replace.
            value (str): The value to set for the specified header.
    
        Notes:
            - If the header already exists, its value will be replaced with the new value.
            - The header name will be automatically converted to lowercase before being stored.
        """
        header = header.lower().strip()
        value = f"{value}".strip()
        self.headers[header] = value

    def get_header(self, header: str, default_value: Optional[str] = None) -> Optional[str]:
        """
        Retrieves the value of a specified header.
    
        This method looks up the given header in the request and returns its value. 
        If the header is not found, it returns the specified `default_value` (or `None` if no default is provided).
    
        Args:
            header (str): The name of the header to retrieve.
            default_value (Optional[str]): The value to return if the header is not found. Defaults to `None`.
    
        Returns:
            Optional[str]: The value of the header if it exists, otherwise the `default_value`.
    
        Notes:
            - If the header does not exist and no `default_value` is provided, `None` will be returned.
        """
        return self.headers.get(header, default_value)
        
    def set_content(self, data: bytes, auto_add_content_headers: bool = True):
        """
        Sets the content of the request.
        This also sets the appropriate content headers if `auto_add_content_headers=True`

        Args:
            data (bytes): Data in bytes to set as content
            auto_add_content_headers (bool): Sets appropriate content headers like Encoding, Content-Length and Content-Type
        """
        self.content_obj.set_content(data, )
        
        if auto_add_content_headers:
            # add content headers
            # For Content-Type and Content-Encoding, try to obtain these from headers but if not set,
            # use values guessed when content was parsed to content_obj
            self.set_header("Content-Length", self.content_obj.size)
            self.set_header(
                "Accept-Encoding",
                self.get_header("content-encoding")
                or self.content_obj.encoding,
            )
            self.set_header(
                "Content-Type",
                self.get_header("content-type")
                or self.content_obj.content_type,
            )
    
    def parse(self, request_data: RequestData):
        """
        Parses request data to the request object
        """
        if not isinstance(request_data, RequestData):
            raise TypeError(f"Expected a RequestData instance, but got {type(request_data).__name__}")
        
        self.request_data = request_data
        self.request_store.update(request_data.request_store)
        
        if isinstance(request_data, RawRequestData):
            self.parse_raw_request(request_data.data)
        else:
            topheader = request_data.headers.pop("topheader")
            self.parse_request(
                topheader=topheader,
                headers=request_data.headers,
                content=request_data.content)
    
    def parse_request(self, topheader: str, headers: Dict[str, str], content: bytes):
        """
        Parse request from topheader, headers and content
        
        Args:
            topheader (str): The request line or topheader containing method, path and http version
            headers (Dict[str, str]): The request headers
            content (bytes): The request body or content
            
        Sets:
            Optional[Exception]): If an error occurs during parsing, it is stored here.
        """
        try:
            self._parse_request(topheader, headers, content)
        except Exception as e:
            if not isinstance(e, RequestSyntaxError) and not isinstance(
                    e, RequestUnsupportedVersionError):
                e = RequestError(f"General request parse error: {e}")
            self.error = e
    
    def parse_raw_request(self, raw_request: bytes):
        """Parse raw request in bytes. If error occurs during parsing, it will be recorded.
    
        This method attempts to parse a raw HTTP request in byte format. If any error
        occurs during the parsing process, the error is captured and stored in the `error` attribute.
    
        Args:
            raw_request (bytes): The raw HTTP request in byte format.
    
        Sets:
            self.error (Optional[Exception]): If an error occurs during parsing, it is stored here.
        """
        assert isinstance(raw_request, bytes), f"Raw request should be in bytes not {type(raw_request)}"
        
        try:
            self._parse_raw_request(raw_request)
        except Exception as e:
            if not isinstance(e, RequestSyntaxError) and not isinstance(
                    e, RequestUnsupportedVersionError):
                e = RequestError(f"General request parse error: {e}")
            self.error = e
    
    def _parse_raw_headers(self, raw_headers: bytes):
        """
        Parses raw HTTP headers from bytes into structured attributes.
    
        This method processes the raw HTTP request headers (excluding content) passed as 
        bytes, and sets relevant instance attributes such as the HTTP method, full path, 
        HTTP version, and individual headers.
    
        It performs the following tasks:
        - Decodes and extracts the HTTP method, path, and version from the top header.
        - Decodes each header line, validates its format, and assigns them to instance headers.
        - Ensures that the HTTP version is supported by the server.
    
        Args:
            raw_headers (bytes): The raw HTTP headers in byte format, typically received
                                  from a client request. The first line contains the HTTP
                                  method, path, and version, followed by headers.
    
        Raises:
            RequestSyntaxError: If the top header or any header is incorrectly formatted.
            RequestUnsupportedVersionError: If the HTTP version is not supported.
        """
        headers_part = raw_headers
        topheader = headers_part[0].strip()
        headers = headers_part[1:]
        
        # Setting some attributes
        self.topheader = topheader = topheader.decode("utf-8").strip()
        
        # Extract method, path, http_version
        if topheader:
            max_splits = 3
            if len(topheader.split(" ", max_splits)) == 3:
                method, path, http_version = topheader.split(" ")
                
                # Decode Fields
                self.method = method
                self.fullpath = url_decode(path)
                self.http_version = http_version
                
            else:
                raise RequestSyntaxError("Bad topheader or payload")
        
        if headers:
            for header in headers:
                if not header.strip():
                    headers_done = True
                
                if len(header.split(b":", 1)) != 2:
                    raise RequestSyntaxError("Bad headers format")
                
                header, value = header.split(b":", 1)
                header, value = (
                    header.decode("utf-8").strip(),
                    value.decode("utf-8").strip(),
                )
                
                # Set Cleaned Headers
                self.set_header(header, value)
        
        # Validate HTTP version
        if self.http_version.upper() not in self.SUPPORTED_HTTP_VERSIONS:
            raise RequestUnsupportedVersionError("Http version not supported")
    
    def _parse_content(self, raw_content: bytes):
        """
        Parses the raw content from a request and sets it as the instance content.
    
        This method processes the raw content passed as bytes, strips any leading and 
        trailing carriage returns or newlines (`\r\n`), and sets it as the content of 
        the request. It does so by calling the `set_content` method, with an option to 
        avoid adding content-related headers automatically.
    
        Args:
            raw_content (bytes): The raw content in byte format that was sent with the 
                                  request. It may represent the body of a POST or PUT 
                                  request, or any data transmitted after the headers.
    
        Notes:
            - This method assumes the content is properly formatted in the request.
            - The stripping of `\r\n` ensures that no unnecessary line breaks remain before 
              storing the content.
            - The method does not automatically add content-related headers (e.g., 
              `Content-Length`) by setting `auto_add_content_headers=False` in the call to 
              `set_content`.
        """
        content = raw_content
        
        if content:
            content = content.strip(b"\r\n")
            self.set_content(content, auto_add_content_headers=False)
    
    def _parse_request(self, topheader: str, headers: Dict[str, str], content: bytes):
        """
        Parses a HTTP request into its components, including headers and body.
    
        Raises:
            RequestSyntaxError: If the request has an invalid format or contains errors.
            RequestUnsupportedVersionError: If the HTTP version is not supported.
        
        Updates:
            - self.COOKIES: Extracted cookies from the request.
            - self.AUTH: Extracted authentication data from the request.
            - self.QUERY: Updated global QueryDict with URL and content query data.
            - self.method.upper(): A QueryDict containing the combined URL and content queries.
        """
        # Setting some attributes
        self.topheader = topheader = topheader.strip()
        
        # Extract method, path, http_version
        max_splits = 3
        
        if len(topheader.split(" ", max_splits)) == 3:
            self.method, self.fullpath, self.http_version = topheader.split(" ")
        else:
             raise RequestSyntaxError("Bad topheader or payload")
        
        # Update Headers
        self.headers.update(headers)
        
        # Validate HTTP version
        if self.http_version.upper() not in self.SUPPORTED_HTTP_VERSIONS:
            raise RequestUnsupportedVersionError("Http version not supported")
    
        # Parse Content
        self._parse_content(content)
        
        # Extract and process request data
        self._extract_and_process_request_data()
        
    def _parse_raw_request(self, raw_request: bytes,):
        """
        Parses a raw HTTP request in byte format into its components, including headers and body.
    
        This method is responsible for taking a raw HTTP request (as bytes) and splitting it 
        into its respective parts: headers, content, and other request data. It then processes 
        each part, including parsing the headers, parsing the content, and extracting necessary 
        data (such as cookies, authentication, and query parameters).
    
        Args:
            raw_request (bytes): The raw HTTP request data in byte format, typically received 
                                  from a client. This includes the HTTP method, path, headers, 
                                  and body/content.
    
        Raises:
            RequestSyntaxError: If the request has an invalid format or contains errors.
        
        Updates:
            - self.COOKIES: Extracted cookies from the request.
            - self.AUTH: Extracted authentication data from the request.
            - self.QUERY: Updated global QueryDict with URL and content query data.
            - self.method.upper(): A QueryDict containing the combined URL and content queries.
        """
        request_parts = raw_request.split(b"\r\n\r\n", 1)

        headers_part = request_parts[0].strip().split(b"\r\n")
        content = request_parts[1] if len(request_parts) > 1 else b""
        
        # Parse Headers
        self._parse_raw_headers(headers_part)
        
        # Parse Content
        self._parse_content(content)
        
        # Extract and process request data
        self._extract_and_process_request_data()
        
    def _extract_and_process_request_data(self):
        """
        Extracts and processes session, authentication, URL queries, and content queries 
        from the incoming request and updates the global QueryDict.
        
        This method handles:
        - Extracting cookies and authentication data from the request.
        - Extracting URL and content-related query parameters.
        - Updating the global `QUERY` dictionary with extracted values.
        - Combining the URL and content queries into a single query and attaching it 
          to the request method as a QueryDict.
    
        Updates:
        - `self.COOKIES`: Extracted cookies from the request.
        - `self.AUTH`: Extracted authentication data from the request.
        - `self.QUERY`: Updated global QueryDict with URL and content query data.
        - `self.method`.upper(): A QueryDict containing the combined URL and content queries.
        """
        # Extract session, auth, and query data
        self.COOKIES = self.extract_cookies_from_request(self)
        self.AUTH = self.extract_auth_from_request(self)
    
        # Extract URL and Content Queries
        self.path, url_query = self.extract_url_queries(self.fullpath)
        content_query = self.extract_content_queries(self)
        
        # Update topheader with decoded url path
        self.topheader = " ".join(
            [self.method.upper(), self.path, self.http_version])
        
        # Update the global QueryDict
        self.QUERY.update({"URL_QUERY": url_query})
        self.QUERY.update({"CONTENT_QUERY": content_query})
        
        # Combine the queries and set as a method attribute (e.g., GET, POST)
        combined_query = url_query.copy()
        combined_query.update(content_query)
        setattr(self, self.method.upper(), QueryDict(combined_query))
        
    def _set_auth_headers(self):
        """Sets 'Authorization' and 'Proxy-Authorization' headers if not already present"""
        auth = self.AUTH.get("auth")
        proxy_auth = self.AUTH.get("proxy_auth")
    
        if auth and not self.get_header("Authorization"):
            self.set_header("Authorization", auth)
    
        if proxy_auth and not self.get_header("Proxy-Authorization"):
            self.set_header("Proxy-Authorization", proxy_auth)
    
    def _build_request_line(self) -> bytes:
        """Construct the request line (method, path, HTTP version)"""
        return f"{self.method.upper()} {self.fullpath} {self.http_version}\r\n".encode("utf-8")
    
    def _build_headers(self) -> bytes:
        """Construct headers for the request"""
        headers = b""
        for header, value in self.headers.items():
            headers += f"{header.title()}: {value.strip()}\r\n".encode("utf-8")
        return headers
    
    def __repr__(self):
        return (f"<{self.__class__.__name__} ("
                f'{self.protocol!r} '
                f"method={self.method!r}, "
                f"path={self.path!r}, "
                f"error={self.error!r}, "
                f"ID={self.ID!r}, "  # unique identifier
                f"content=..., "  # Truncated content representation
                f"query=...)>"  # Truncated query representation
                )[:]


class HttpProxyRequest(Request):
    """
    This is the basic HttpProxyRequest.

    This kind of request may contain 2 http requests in single http request.

    Example:
    
    ```py
    CONNECT /192.xxx.xxx.xxx HTTP/1.1\r\n\r\nGET / HTTP/2.1\r\n\r\nHost: xxx.com\r\nConnection: Keep-Alive
    ```
    
    Not Implemented yet!
    """


HttpRequest = Request  # alias for Request
