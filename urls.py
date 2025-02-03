"""
This contains URL patterns to register for the application.
"""
from duck.urls import re_path, path
from . import views


urlpatterns = [
    path("/", views.home_view, name="home"),
]
