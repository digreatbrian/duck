from duck.http.middlewares.contrib.session import SessionMiddleware
from duck.http.middlewares.contrib.django import DjangoHeaderFixerMiddleware
from duck.http.middlewares.contrib.www_redirect import WWWRedirectMiddleware

__all__ = [
    'SessionMiddleware',
    'DjangoHeaderFixerMiddleware',
    'WWWRedirectMiddleware',
]
