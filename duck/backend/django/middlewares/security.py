"""Proxy module for Django SecurityMiddleware"""

from duck.utils.importer import x_import

SecurityMiddleware = x_import("django.middleware.security.SecurityMiddleware")
