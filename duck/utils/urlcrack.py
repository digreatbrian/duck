"""
URLCrack - A lightweight module providing a robust URL class for parsing and manipulating URLs without relying on the `urllib` module. 

This module handles URLs gracefully, even those without a scheme, addressing limitations found in `urllib.parse` and similar libraries.

## Features:
- Parse and manipulate URLs effortlessly.
- Supports URLs with or without schemes.
- Easily update host, port, query, and other components.

``` {note}
This method is more reliable than `urllib` and similar packages, as they often struggle to handle URLs that lack a scheme (e.g., `https`).
```

## Example Usage:

```py
from urlcrack import URL

url_obj = URL('digreatbrian.tech/some/path?query=something#resource')

# Manipulate the URL object
url_obj.host = "new_site.com"
url_obj.port = 1234  # Set port to None to remove it
    
print(url_obj.to_str()) 
# Output: new_site.com:1234/some/path?query=something#resource
```

## Author:
Brian Musakwa <digreatbrian@gmail.com>
"""

import re
import os

from typing import Tuple, Union, Optional, List


__author__ = "Brian Musakwa"
__email__ = "digreatbrian@gmail.com"


class InvalidURLPathError(Exception):
    """
    Raised when the URL path is invalid or does not meet expected criteria.
    """
    pass


class InvalidURLError(Exception):
    """
    Raised when the URL is invalid or improperly formatted.
    """
    pass


class InvalidURLAuthorityError(Exception):
    """
    Raised when the authority (netloc) of the URL is invalid.
    """
    pass
    

class InvalidPortError(Exception):
    """
    Raised when the port of the URL is invalid.
    """
    pass


def joinpaths(path1: str, path2: str, *more):
    """
    Returns joined paths but makes sure all paths are included in the final path rather than os.path.join
    """
    path1 = path1.rstrip("/")
    path2 = path2.lstrip("/")  # clean paths
    finalpath = os.path.join(path1, path2)

    for p in more:
        finalpath = finalpath.rstrip("/")
        p = p.lstrip("/")
        finalpath = os.path.join(finalpath, p)
    return finalpath


class URL:
    """
    Lightweight URL class for manipulating and parsing URLs.
    
    This class works on urls without scheme unlike urllib.parse and other libraries.
    """
    def __init__(self, url: str, normalize_url: bool = True):
        self.scheme = ''
        self.netloc = ''
        self.path = ''
        self.query = ''
        self.fragment = ''
        self.parse(url, normalize_url)
    
    @property
    def user_info(self) -> Optional[str]:
        """
        Returns the user info like username@passwd in URL.
        """
        if '@' in self.netloc:
            user_info, host = self.netloc.rsplit('@', 1)
            return user_info or None
    
    @property
    def host(self) -> Optional[str]:
        """
        Returns the host (excluding port) from the URL object.
        """
        if self.netloc:
            host, port = self.split_host_and_port(self.netloc)
            if '@' in host:
                user_info, host = host.rsplit('@', 1)
            return host or None
    
    @host.setter  
    def host(self, host: str):
        """
        Sets the URL host eg (some-host.com).
        """
        if self.netloc:
            old_host, port = self.split_host_and_port(self.netloc)
            user_info = self.user_info
            if port:
                if user_info:
                    self.netloc = f'{user_info}@{host}:{port}'
                else:
                    self.netloc = f'{host}:{port}'
            else:
                if user_info:
                    self.netloc = f'{user_info}@{host}'
                else:
                    self.netloc = f'{host}'
        else:
            self.netloc = str(host)
     
    @property
    def port(self) -> Optional[int]:
        """
        Returns the port from the URL object.
        """
        if self.netloc:
            host, port = self.split_host_and_port(self.netloc)
            return port or None
    
    @port.setter  
    def port(self, port: int):
        """
        Sets the port in URL authority (netloc).
        """
        if self.netloc:
            host, old_port = self.split_host_and_port(self.netloc)
            user_info = self.user_info
            if not port:
                if user_info:
                    self.netloc = f'{user_info}@{host}'
                else:
                    self.netloc = f'{host}'
            else:
               if user_info:
                    self.netloc = f'{user_info}@{host}:{port}'
               else:
                    self.netloc = f'{host}:{port}'
        else:
            raise InvalidURLAuthorityError("Cannot set port for URL without authority (port)")
    
    @classmethod
    def urljoin(
        cls,
        base_url: str,
        head_url: str,
        replace_authority: bool = False,
        full_path_replacement: bool = True,
     ):
        """
        Joins 2 URLs and return the result.
        
        Notes:
            If both URLs has schemes, The new URL will contain the base URL scheme.
        
        Args:
            base_url (str): The base URL
            head_url (str): The URL or URL path to concanetate to the base URL
            replace_netloc (bool):
                Whether to replace URL authority (netloc). If head url has a netloc, it will be the final netloc and this also replaces the
                final scheme if it is present in head URL. Defaults to False.
            full_path_replacement (bool):
                This means whether to replace the query and fragment even if they are empty in head URL. Defaults to True.
            
        Example:
            > https://digreatbrian.tech/some/path + http://digreatbrian.tech/path/endpoint = https://digreatbrian.tech/some/path/endpoint
        """
        base_url_obj = URL(base_url)
        head_url_obj = URL(head_url)
        
        if head_url_obj.scheme:
            base_url_obj.scheme = head_url_obj.scheme
        
        if replace_authority or not base_url_obj.netloc:
            if head_url_obj.netloc:
                base_url_obj.netloc = head_url_obj.netloc
        
        if head_url_obj.path:
            if not base_url_obj.path or base_url_obj.path == '/':
                base_url_obj.path = head_url_obj.path
            else:
                base_url_obj.path = joinpaths(base_url_obj.path, head_url_obj.path)
            if full_path_replacement:
                base_url_obj.query = head_url_obj.query
                base_url_obj.fragment = head_url_obj.fragment
            else:
                if head_url_obj.query:
                    base_url_obj.query = head_url_obj.query
                if head_url_obj.fragment:
                    base_url_obj.fragment = head_url_obj.fragment
        return base_url_obj.to_str()
    
    @classmethod
    def normalize_url_path(cls, url_path: str, ignore_chars: Optional[List[str]]=None):
        """
        This normalizes the URL path.
        """
        return URL.normalize_url('/' + url_path, ignore_chars)
        
    @classmethod
    def normalize_url(cls, url: str, ignore_chars: Optional[List[str]]=None):
        """
        Normalizes a URL by removing consecutive slashes, adding a leading slash, removing trailing slashes, removing disallowed characters, e.g "<", string quotes (etc), replacing back slashes and lowercasing the scheme.
        """
        is_url_path = False
        ignore_chars = ignore_chars or []
        
        if not url:
            # url is None
            url = ""
        disallowed_chars = ("<", '"', "'", "^", ">", ";", "|", "{", "}", "`", " ")
        url = url.replace("\\", "/")
    
        # removing disallowed characters
        for i in disallowed_chars:
            if i not in ignore_chars:
                url = url.replace(i, "")
    
        # For urls in form "GET /] HTTP/1.1", or  "GET /],app-emailsubscribe,app-newsletter-widget,div.newsletter-image,div[data-newsletter-1],div[data-newsletter-2],gannett-atoms-component-newsletter-cta,hl-newsletter-cta,div HTTP/1.1"
        # The urls in form above may be provided by other browsers like 1DM
        if "," in url:
            url = url.split(",")[0].strip("]")
       
        if not url or url.startswith('/'):
            is_url_path = True
        
        url_obj = URL(url, normalize_url=False)
        normalized_path = re.sub(r"/+", "/", "/" + url_obj.path.strip("/"))
        url_obj.path = normalized_path
        url_str = url_obj.to_str()
        
        if is_url_path and not url_str.startswith('/'):
            url_str = '/' + url_str
        return url_str
    
    def split_host_and_port(self, authority: str, convert_port_to_int: bool = True) -> Tuple[str, Union[str, int]]:
        """
        Returns the host and port from authority (netloc).
        
        Args:
            authority (str): The authority or netloc (usually in form 'some-host:port')
            convert_port_to_int (bool): Whether to automatically convert port to integer (only if port found). Defaults to True.
        
        Returns:
            Tuple: Tuple containing host and port.
        """
        try:
            scheme, netloc, leftover = self.split_scheme_and_authority(authority)
            if scheme:
                raise InvalidURLAuthorityError("URL Authority or Netloc must not contain scheme (eg. 'https://').")
        except InvalidURLError:
            raise InvalidURLAuthorityError("URL Authority or Netloc is not found, make sure authority doesn't start with 'scheme://' or forward slash ('/').")
        
        host, port = '', ''
        
        # Take account for IPV6 hosts
        if '[' and ']:' in authority:
            host, port = authority.rsplit(']:', 1)
        else:
            if ':' in authority:
                host, port = authority.rsplit(':', 1)
            else:
                host = authority
        if port and convert_port_to_int:
            try:
                port = int(port)
            except ValueError as e:
                raise InvalidPortError(f"Port obtained from authority (netloc) cannot be converted to integer: {e}")
        return host, port
        
    def innerjoin(self, head_url: str):
        """
        Join the current URL with the provided `head_url`, and update the current URL object in-place.
    
        Args:
            head_url (str): The relative or absolute URL segment to join with the current URL.
    
        Behavior:
        - Performs a URL join operation similar to urllib.parse.urljoin.
        - The resulting URL replaces the current URL in this object.
        - Useful for modifying the current object without creating a new instance.
    
        Returns:
            self: The current URL object with the updated value.
        """
        new_url = URL.urljoin(self.to_str(), head_url)
        self.parse(new_url)
        return self
    
    def join(self, head_url: str):
        """
        Join the current URL with the provided `head_url`, and return a new URL object.
    
        Args:
            head_url (str): The relative or absolute URL segment to join with the current URL.
    
        Behavior:
        - Performs a URL join operation similar to urllib.parse.urljoin.
        - Unlike `innerjoin()`, this does not modify the current object.
        - Returns a new instance with the resulting joined URL.
    
        Returns:
            URL: A new URL object with the combined URL.
        """
        new_url = URL.urljoin(self.to_str(), head_url)
        return URL(new_url)
    
    def split_scheme_and_authority(self, url: str) -> Tuple[str, str, str]:
        """
        Returns the scheme, authority  (netloc) and leftover (which might be the path most of the time) from a valid URL.
        
        Returns:
            Tuple: A tuple containing scheme, netloc and leftover (mostly the path).
        """
        scheme, netloc, leftover = '', '', ''
        
        if '://' in url:
           scheme, url = url.split('://', 1)
           if '/' in url:
               # URL form https://something/
               # something/
               netloc, url = url.split('/', 1)
               leftover = '/' + url
           else:
               # URL form https://something
               # something
               netloc = url
        else:
           if not url.startswith('/'):
               if  '/' in url:
                   netloc, leftover = url.split('/', 1)
                   leftover = '/' + leftover
               else:
                   netloc = url
        
        if not (scheme or netloc):
            raise InvalidURLError("URL invalid, should startwith a scheme (e.g 'https' or just the host). This might be a path being parsed here.")
        
        if '@' in scheme:
            # scheme has been left in this format 'user:pwd@https'
            user_info, scheme = scheme.rsplit('@', 1)
            netloc = '@'.join([user_info, netloc])
        
        return scheme, netloc, leftover
        
    def split_path_components(self, url_path: str) -> Tuple[str, str, str]:
        """
        Returns the path components from a url path.
        
        Returns:
            Tuple: The tuple containg path, query and fragment.
        """
        try:
            scheme, netloc, url_path = self.split_scheme_and_authority(url_path)
            if scheme:
                raise InvalidURLPathError("URL Path must not include a scheme.")
            if netloc:
                raise InvalidURLPathError("URL Path must start with a forward slash '/'.")
        except InvalidURLError:
            # Confirmation that this is a valid path
            pass
        
        path, query, fragment = '', '', ''
        
        if '?' in url_path:
            path, url_path = url_path.split('?', 1)
            if '#' in url_path:
                query, fragment = url_path.split('#', 1)
            else:
                query = url_path
        else:
            if '#' in url_path:
                path, fragment = url_path.split('#', 1)
            else:
                path = url_path
        return path, query, fragment
    
    def parse(self, url: str, normalize_url: bool = True):
        """
        Parse URL from a string.
       
        Args:
           normalize_url (bool): Whether to normalize the URL e.g:
               https://// \\google.com>}////path?q`=some_query``; => https://google.com/path?q=some_query
       
        Expected input:
           scheme://some-site.com/path/...
           scheme://some-site/...
           some-site.com/...
           /some-path/...
        """
        query, fragment = '', ''
       
        if normalize_url:
            url = URL.normalize_url(url)
       
        try:
            scheme, netloc, path = self.split_scheme_and_authority(url)
        except InvalidURLError:
            # The url parsed is a URL path instead.
            scheme = ''
            netloc = ''
            path = url
           
        if path:
            path, query, fragment = self.split_path_components(path)
       
        # Set attributes
        self.scheme, self.netloc, self.path, self.query, self.fragment = (
           scheme, netloc, path, query, fragment)
    
    def to_str(self) -> str:
        """
        Converts the current URL object to string.
        """
        url = ''
        
        if self.scheme:
            url += self.scheme + '://'
        
        if self.netloc:
            url += self.netloc
        
        if self.path:
            url += self.path
            # Only add query or fragment if path exists
            if self.query:
                url += '?' + self.query
            if self.fragment:
                url += '#' + self.fragment
        if self.netloc:
            url = url.strip('/')
        return url
        
    def __repr__(self):
        """
        Returns a string representation of the URL.

        Returns:
            str: String representation of the URL.
        """
        return (
            f"<{self.__class__.__name__} scheme='{self.scheme}' "
            f"netloc='{self.netloc}' "
            f"path='{self.path}' "
            f"query='{self.query}' "
            f"fragment='{self.fragment}'>"
        )
