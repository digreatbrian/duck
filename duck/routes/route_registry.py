"""
Class for registering routes/url_patterns/urls/paths
"""

import re
import functools

from typing import Dict, Optional, Dict, Callable, List
from collections import defaultdict

from duck.exceptions.all import (
    RouteError,
    RouteNotFoundError,
)
from duck.utils.path import (
    normalize_url_path,
    is_good_url_path,
)


class BaseRouteRegistry:
    """
    A registry for storing and retrieving routes (URL patterns) with associated handlers.

    This registry supports wildcard patterns (*), automatically replacing angle bracket placeholders like <name> with wildcards. It ensures uniqueness of routes both by name and by URL pattern.
    """

    url_map = defaultdict(
        dict)  # {normalized_url: {name: (handler, methods, pattern)}}
    """Mapping of URLs to route details"""

    def __init__(self):
        pass

    def extract_kwargs_from_url(self, url: str, registered_url: str) -> dict:
        """
        Extracts dynamic parameters from a URL based on a registered URL pattern.
    
        ### Example:
        
        Given:
        
        - **url**: `/articles/what-is-money/1/`
        - **registered_url**: `/articles/<name>/<article-number>/`
        
        This function identifies and extracts dynamic values based on placeholders
        in the registered URL pattern.
    
        **How it works:**
        - `<name>` captures `what-is-money`
        - `<article-number>` captures `1`
        
        The result is a dictionary:
        
        ```py
        {
            "name": "what-is-money",
            "article-number": "1"
        }
        ```
    
        ### Edge Case:
        If the registered pattern ends with a dynamic placeholder (`/<path>`), 
        the remaining part of the URL is assigned to that variable. 
    
        Example:
        
        - **url**: `/files/user/docs/readme.txt`
        - **registered_url**: `/files/<path>`
        
        Produces:
        
        ```py
        {"path": "user/docs/readme.txt"}
        ```
    
        Args:
            url (str): The actual URL to process.
            registered_url (str): The template pattern containing placeholders.
    
        Returns:
            dict: A dictionary of extracted parameters and their corresponding values.
    
        Raises:
            RouteError: If the provided URL does not match the registered pattern.
        """
        _url = re.sub(r"<[^>]+>", "*", url)  # Replace placeholders with '*' to create a matchable pattern
        pattern = re.compile(re.escape(_url).replace(r"\*", ".*"))  # Convert '*' into regex wildcard
    
        if not pattern.fullmatch(_url):
            raise RouteError("Provided URL does not match the registered pattern")
    
        parts = url.strip("/").split("/")  # Normalize URL by removing leading/trailing slashes and splitting by '/'
        parts_b = registered_url.strip("/").split("/")  # Normalize registered pattern in the same way
        kwargs = {}
    
        for i, part in enumerate(parts_b):
            if part.startswith("<") and part.endswith(">"):  # Identify placeholders
                arg_name = part.strip("<>")  # Extract variable name from '<var>'
                value = parts[i]
    
                # Handle cases where a dynamic placeholder might capture the remaining path
                # Example: `/files/user/docs/readme.txt` should match `/files/<path>`
                if i == len(parts_b) - 1:  # If it's the last placeholder in the pattern
                    value = "/".join(parts[i:])  # Capture everything remaining in the URL
    
                kwargs[arg_name] = value  # Store extracted value
    
        return kwargs
    
    def regex_register(
        self,
        re_url: str,
        handler: Callable,
        name: Optional[str] = None,
        methods: Optional[List[str]] = None,
        **kw):
        """Registers a Regular expression route

        Args:
            re_url (str): Regular expression route (e.g /some/path/.*)
            handler (Callable): The view or handler for the route.
            name (Optional[str]): The name for the route. (optional)
            methods (Optional[List[str]]): The supported methods for the route. Defaults to None to support all methods.
        """
        re_url = "/" + re_url if not (re_url.startswith('/') or re_url.startswith('\\')) else re_url
        methods = methods or []
        
        assert callable(
            handler), f"Handler argument should be a callable not '{handler}' "
        
        if not name:
            name = f"route_{len(self.url_map) + 1}"  # Auto-generate names

        pattern = re_url

        # check for conflicts with existing patterns
        for (
                registered_url,
                route_info,
        ) in self.url_map.items():  # iterate over registered URLs
            for registered_name, (
                    _,
                    _,
                    existing_pattern,
            ) in route_info.items():
                if name == registered_name:
                    raise RouteError(
                        f"URL '{re_url}' with name '{name}' already registered."
                    )
                if existing_pattern.fullmatch(re_url) or re.compile(
                        pattern).fullmatch(registered_url):
                    raise RouteError(
                        f"Regex URL '{re_url}' conflicts with existing registered route '{registered_url}'."
                    )
        type(self).url_map[re_url][name] = (
            handler,
            methods,
            re.compile(pattern),
        )

    def register(
         self,
         url_path: str,
         handler: Callable,
         name: Optional[str] = None,
         methods: Optional[List[str]] = None,):
        """Registers a Regular expression route

        Args:
            url_path (str): Regular expression route (e.g /some/path/.*)
            handler (Callable): The view or handler for the route.
            name (Optional[str]): The name for the route. (optional)
            methods (Optional[List[str]]): The supported methods for the route. Defaults to None to support all methods.
            
        Raises:
                RouteError: If a route with the same name or conflicting URL pattern already exists or a Bad URL path
                AssertionError: If handler argument is not a Callable
        """
        methods = methods or []
        
        assert callable(
            handler
        ), f"Handler/View argument should be a callable not '{handler}' "
        
        if "*" in url_path:
            raise RouteError(
                f"Aterisks not supported, please use method regex_register instead. Route: {url_path}"
            )

        original_url = url_path
        
        # Replace placeholders with wildcard aterisk (*)
        url_path = re.sub(r"<[^>]+>", "*", url_path)
        
        normalized_url = normalize_url_path(url_path.strip("/"))
        normalized_original_url = normalize_url_path(original_url, ignore_chars=["<", ">"])

        if not name:
            name = f"route_{len(self.url_map) + 1}"  # Auto-generate names

        # convert wildcards to regex patterns
        pattern = re.escape(normalized_url).replace(r"\*", ".*")

        # check for conflicts with existing patterns
        for (
                registered_url,
                route_info,
        ) in self.url_map.items():  # iterate over registered URLs
            for registered_name, (
                    _,
                    _,
                    existing_pattern,
            ) in route_info.items():
                if name == registered_name:
                    raise RouteError(
                        f"URL '{url_path}' with name '{name}' already registered.")
                if existing_pattern.fullmatch(normalized_url) or re.compile(
                        pattern).fullmatch(registered_url):
                    raise RouteError(
                        f"URL '{url_path}' conflicts with existing registered route '{registered_url}'."
                    )
        type(self).url_map[normalized_original_url][name] = (
            handler,
            methods,
            re.compile(pattern),
        )

    @functools.lru_cache(maxsize=75)
    def fetch_route_info_by_name(self, name: str) -> Dict:
        """Fetches the handler, allowed methods, URL pattern for a route, etc by its name

        Note: this does not generate any handler kwargs because a real URL is needed not a Name only

        Args:
                name (str): The name of the route to retrieve.

        Returns:
                Dict: A dictionary containing the name, handler function, handler keyword arguments, a list of allowed methods, and the URL pattern.

        Raises:
                RouteNotError: If no route with the given name is found.

        """
        for registered_url, routes in self.url_map.items():
            for registered_name, route_details in routes.items():
                if registered_name == name:
                    handler, methods, pattern = route_details
                    return {
                        "name": registered_name,
                        "url": registered_url,
                        "handler": handler,
                        "methods": methods,
                        "pattern": pattern,
                        "handler_kwargs": {},
                    }
        raise RouteNotFoundError(f'Route with name "{name}" not found')

    @functools.lru_cache(maxsize=75)
    def fetch_route_info_by_url(self, url_path: str) -> Dict:
        """Fetches the handler and allowed methods for a given URL path.

        This generates handler kwargs rather than method fetch_route_info_by_name

        Args:
                url_path (str): The URL path to match.

        Returns:
                Dict: A dictionary containing the route details.

        Raises:
                RouteNotFoundError: If no matching route is found.
                RouteError: If URL in bad format
        """
        normalized_url = normalize_url_path(url_path)
        
        if not is_good_url_path(normalized_url):
            raise RouteError(
                f"Bad URL path provided, should be in form '/path/subpath/' not '{url}' "
            )

        for registered_url, routes in self.url_map.items():
            for name, (handler, methods, pattern) in routes.items():
                if pattern.fullmatch(normalized_url):
                    return {
                        "name": name,
                        "url": registered_url,
                        "handler": handler,
                        "methods": methods,
                        "pattern": pattern,
                        "handler_kwargs": self.extract_kwargs_from_url(normalized_url, registered_url),
                    }
        raise RouteNotFoundError(
            f'Route "{url_path}" doesn\'t match any registered routes')


RouteRegistry = BaseRouteRegistry()
