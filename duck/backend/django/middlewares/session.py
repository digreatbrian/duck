"""
Proxy middleware for Django SessionMiddleware
"""

from django.contrib.sessions.middleware import (
    SessionMiddleware as DjangoSessionMiddleware,
)
from duck.utils.importer import x_import

SessionMiddleware = x_import(
    "django.contrib.sessions.middleware.SessionMiddleware")
