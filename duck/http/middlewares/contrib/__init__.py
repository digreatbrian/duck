from duck.http.middlewares.contrib.session import SessionMiddleware
from duck.http.middlewares.contrib.django import DjangoHeaderFixerMiddleware


__all__ = [
    'SessionMiddleware',
    'DjangoHeaderFixerMiddleware',
]
