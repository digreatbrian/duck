""""
Functions for easy creation and organization of url patterns data.

Example usage:

```py
# urls.py
from duck.urls import path, re_path
from duck.shortcuts import render
from duck.http.response import HttpResponse
	
def home_view(request):
	return HttpResponse("Hello world")
	
def profile_view(request, user_id):
	return render('profile.html', request, context={'user_id': user_id})
	
def documents_view(request):
	return f"Document {request.path}"
	
urlpatterns = [
    path('/', home_view, name='home', methods=['GET']),
    path("/user/<user_id>/profile", profile_view, name='profile'),
    re_path('/doc/.*', documents_view, name='docs', methods=['GET'])
]
```
"""
from typing import List, Callable, Optional


class URLPattern(dict):
    """
    A custom dictionary to represent a URL pattern.
    It allows easy access to URL, handler, name, and methods.
    """

    def __init__(self, url: str, handler: Callable, name: Optional[str], methods: List[str], regex: bool = False):
        super().__init__()
        self["url"] = url
        self["handler"] = handler
        self["name"] = name
        self["methods"] = methods
        self["regex"] = regex
   
    @property
    def regex(self):
        return self.get('regex', False)
    
    def __repr__(self):
        """
        Returns a string representation of the URLPattern.

        Returns:
            str: String representation of the URLPattern.
        """
        return f"<{self.__class__.__name__} {super().__repr__()}>"


def path(
    url: str,
    view: Callable,
    name: Optional[str] = None,
    methods: Optional[List[str]] = None,
) -> URLPattern:
    """
    Function to easily store urlpattern data for easy Route registration
    """
    methods = methods or []
    
    return URLPattern(**{
        "url": url,
        "handler": view,
        "name": name,
        "methods": methods,
    })


def re_path(
    re_url: str,
    view: Callable,
    name: Optional[str] = None,
    methods: Optional[List[str]] = None,
) -> URLPattern:
    """
    Function to easily store urlpattern data for easy Route registration
    """
    methods = methods or []
    
    return URLPattern(**{
        "url": re_url,
        "handler": view,
        "name": name,
        "methods": methods,
        "regex": True,
    })
