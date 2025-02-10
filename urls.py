"""
This contains URL patterns to register for the application.
"""
from duck.urls import re_path, path


import views


urlpatterns = [
    path("/", views.home_view, name="home"),
    path("/about", views.about_view, name="about"),
    path("/contact", views.contact_view, name="contact"),
]
