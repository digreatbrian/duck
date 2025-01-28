"""
Module containing Duck's React fronted blueprint.

This blueprint will only serve scripts and jsx code if the a template with the
`react_frontend` tag has been rendered. The `react_frontend` template tag registers 
scripts and jsx code ready to be served.
"""
# yapf: disable
from duck.routes import Blueprint
from duck.settings import SETTINGS
from duck.urls import path
from duck.utils.path import joinpaths

from . import views


FRONTEND = SETTINGS["FRONTEND"]

urlpatterns = []
if FRONTEND:
    root_url = FRONTEND["REACT"]["root_url"]
    scripts_url = FRONTEND["REACT"]["scripts_url"]
    scripts_url = joinpaths(root_url, scripts_url)  # Final URL endpoint for serving React scripts defined in settings.py.
    urlpatterns = [
        path(
            root_url,
            views.jsx_code_view,
            name="react_jsx_code",
            methods=["GET"],
        ), # Urlpattern for serving jsx code registered with "react_fronted" template tag.
        path(
            scripts_url,
            views.react_scripts_view,
            name="react_scripts",
            methods=["GET"],
        ), # Urlpattern for serving React scripts defined in settings.py
    ]

ReactFrontend = Blueprint(
    location=__file__,
    name="react_frontend",
    urlpatterns=urlpatterns,
    prepend_name_to_urls=False,
    is_builtin=True,
    enable_template_dir=False,
    enable_static_dir=False,
)
