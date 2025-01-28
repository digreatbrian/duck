"""Module to proxy django common middleware"""

from duck.utils.importer import x_import

CommonMiddleware = x_import("django.middleware.common.CommonMiddleware")
