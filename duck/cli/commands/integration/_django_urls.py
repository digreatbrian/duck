"""
Django URL Patterns Registration Module

This module is utilized by Django to register URL patterns using the Duck framework.

WARNING: Do not overwrite the `urlpatterns` variable as it contains all URL patterns registered using Duck.

Instead of overwriting `urlpatterns`, append your new URL patterns to the list.

Example Usage:
--------------
from duck.backend.django import urls as duck_urls

# Append new URL patterns
urlpatterns = duck_urls.urlpatterns + [
    # Your new URL patterns here
]
"""
from duck.backend.django import urls as duck_urls

old_urlpatterns = []

try:
    from .old.urls import urlpatterns as old_urlpatterns    
except (ImportError, ModuleNotFoundError):
    pass
         
urlpatterns = duck_urls.urlpatterns + old_urlpatterns
