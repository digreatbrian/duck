"""
Module containing Duck's essesntials blueprint.
"""
# yapf: disable
from duck.routes import Blueprint
from duck.settings import SETTINGS
from duck.urls import re_path
from duck.utils.path import normalize_url_path

from . import views


STATIC_URL = normalize_url_path(str(SETTINGS["STATIC_URL"])) + "/"

MEDIA_URL = normalize_url_path(str(SETTINGS["MEDIA_URL"])) + "/"


MediaFiles = Blueprint(
    location=__file__,
    name="media",
    urlpatterns=[
        re_path(
            f"{MEDIA_URL}.*",
            views.mediafiles_view,
            name="mediafiles",
            methods=["GET"],
        ),
    ],
    prepend_name_to_urls=False,
    is_builtin=True,
    enable_template_dir=False,
    enable_static_dir=False,
)


StaticFiles = Blueprint(
    location=__file__,
    name="static",
    urlpatterns=[
        re_path(
            f"{STATIC_URL}.*",
            views.staticfiles_view,
            name="staticfiles",
            methods=["GET"],
        ),
    ],
    prepend_name_to_urls=False,
    is_builtin=True,
    enable_template_dir=False,
    enable_static_dir=False,
)
