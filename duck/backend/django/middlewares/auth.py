"""
Proxy module for Django AuthenticationMiddleware.
"""

from duck.utils.importer import x_import

AuthenticationMiddleware = x_import(
    "django.contrib.auth.middleware.AuthenticationMiddleware")
