"""
Module containing staticfiles view.
"""
import os
from typing import List, Optional

from duck.routes import Blueprint
from duck.settings import SETTINGS
from duck.http.request import HttpRequest
from duck.http.response import FileResponse
from duck.shortcuts import not_found404
from duck.utils.path import joinpaths, normalize_url_path


STATIC_ROOT = str(SETTINGS["STATIC_ROOT"])

def dev_find_staticfile(staticfile: str) -> Optional[str]:
    """
    Find staticfile in development mode.
    """
    from duck.cli.commands.collectstatic import CollectStaticCommand
    
    global_static_dirs = SETTINGS["GLOBAL_STATIC_DIRS"]
    blueprint_static_dirs: List[str, Blueprint] = list(CollectStaticCommand.find_blueprint_static_dirs())
    
    for static_dir in global_static_dirs:
        staticfile = joinpaths(str(static_dir), staticfile)
        if os.path.isfile(staticfile):
            return staticfile
    
    for file in blueprint_static_dirs:
        staticfile = joinpaths(file, staticfile)
        if os.path.isfile(staticfile):
            return staticfile
            

def staticfiles_view(request: HttpRequest):
    """
    Staticfiles view.
    """
    staticfile = normalize_url_path(request.path)
    if staticfile.count("/") > 1:
        staticfile = "/".join(staticfile.split("/", 2)[2:])
    
    if SETTINGS["DEBUG"]:
        staticfile = dev_find_staticfile(staticfile)
    else:
        staticfile = joinpaths(STATIC_ROOT, staticfile)
    
    if not os.path.isfile(staticfile or ""):
        response = not_found404(body=f"<p>Nothing matches the provided URI: {request.path}</p>Consider using command <strong>collectstatic</strong> to add this to static files.</p>")
        return response
    
    return FileResponse(staticfile)
