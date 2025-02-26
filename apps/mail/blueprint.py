
from duck.routes import Blueprint
from duck.urls import path, re_path

from . import views

Mail = Blueprint(
    location=__file__,
    name="mail",
    urlpatterns=[],
    prepend_name_to_urls=True,
    enable_static_dir=False,
    enable_template_dir=True,
    static_dir="static",
)
