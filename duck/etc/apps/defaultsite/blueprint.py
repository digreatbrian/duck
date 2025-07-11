"""
Module containing Duck's default site blueprint.
"""

from duck.routes import Blueprint
from duck.urls import path, re_path

from . import views

DuckSite = Blueprint(
    location=__file__,
    name="ducksite",
    urlpatterns=[
        path("/", views.ducksite_home_view, name="home"),
        path("/contact", views.ducksite_contact_view, name="contact"),
        path("/about", views.ducksite_about_view, name="about"),
        path("/speedtest", views.ducksite_speedtest_view, name="speedtest"),
        re_path(
            "/duck-static/.*",
            views.ducksite_staticfiles_view,
            name="duck-staticfiles",
            methods=["GET"],
        ),
    ],
    prepend_name_to_urls=False,
    is_builtin=True,
    enable_static_dir=True,
    enable_template_dir=True,
    static_dir="shared_static",  # includes only static files that needs to be shared or stored in static root.
)

# The above blueprint will only allow collectstatic method to collect static files in shared_static because some parts of the duck app depends on these shared static files.
