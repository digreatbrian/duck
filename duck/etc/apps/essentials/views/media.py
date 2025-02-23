"""
Module containing mediafiles view.
"""

import os

from duck.http.request import HttpRequest
from duck.http.response import FileResponse
from duck.settings import SETTINGS
from duck.utils.path import (
    joinpaths,
    normalize_url_path,
)
from duck.shortcuts import not_found404


MEDIA_ROOT = str(SETTINGS["MEDIA_ROOT"])


def mediafiles_view(request: HttpRequest, ):
    """
    Mediafiles view.
    """
    mediafile = normalize_url_path(request.path)
    if mediafile.count("/") > 1:
        mediafile = "/".join(mediafile.split("/", 2)[2:])
    mediafile = joinpaths(MEDIA_ROOT, mediafile)

    if not os.path.isfile(mediafile):
        response = not_found404(body=f"<p>Nothing matches the provided URI: {request.path}</p>")
        return response
    return FileResponse(mediafile)
