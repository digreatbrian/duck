"""Module to proxy django clickjacking xframe options middleware"""

from duck.utils.importer import x_import

XFrameOptionsMiddleware = x_import(
    "django.middleware.clickjacking.XFrameOptionsMiddleware")
