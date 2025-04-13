"""
Module containing Duck's Certbot blueprint - For obtaining, verifying and renewing ssl certificate from letsencrypt.com.
"""
# yapf: disable
from duck.routes import Blueprint
from duck.urls import re_path

from . import views


Certbot = Blueprint(
    location=__file__,
    name="certbot",
    urlpatterns=[
        re_path(
            f"/.well-known/.*",
            views.webroot_view,
            name="webroot",
            methods=["GET"],
        ),
    ],
    prepend_name_to_urls=False,
    is_builtin=True,
    enable_template_dir=False,
    enable_static_dir=False,
)
