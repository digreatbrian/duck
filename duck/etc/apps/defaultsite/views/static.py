"""
Module containing Duck's default site staticfiles view.
"""

import os
import pathlib

from duck.http.request import HttpRequest
from duck.http.response import FileResponse
from duck.utils.path import (
    joinpaths,
    normalize_url_path,
)
from duck.shortcuts import not_found404


STATIC_ROOT = str(pathlib.Path(__file__).resolve().parent.parent / "static")


def ducksite_staticfiles_view(request: HttpRequest, ):
    """
    Staticfiles view for the Duck's default site.
    """
    staticfile = normalize_url_path(request.path)
    if staticfile.count("/") > 1:
        staticfile = "/".join(staticfile.split("/", 2)[2:])
    staticfile = joinpaths(STATIC_ROOT, staticfile)
    
    if not os.path.isfile(staticfile):
        response = not_found404(body=f"<p>Nothing matches the provided URI: {request.path}</p>")
        return response
    return FileResponse(staticfile)
