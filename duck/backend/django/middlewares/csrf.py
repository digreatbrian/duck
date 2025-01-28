"""Module to proxy django csrfview middleware"""

from duck.utils.importer import x_import

CsrfViewMiddleware = x_import("django.middleware.csrf.CsrfViewMiddleware")
