"""Module to proxy django message middleware"""

from duck.utils.importer import x_import

MessageMiddleware = x_import(
    "django.contrib.messages.middleware.MessageMiddleware")
