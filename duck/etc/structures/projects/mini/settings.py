"""
File containing settings for Duck application.
"""
# yapf: disable
import os
import json
import pathlib

from duck.etc.middlewares import middlewares
from duck.etc.normalizers import normalizers
from duck.secrets import DUCK_SECRET, SECRET_DOMAIN
from duck.storage import duck_storage


# Base directory where the Duck application is running from
BASE_DIR: str | pathlib.Path = pathlib.Path(__file__).resolve().parent


# SECURITY WARNING: Keep the secret key used in production secret!
# Modify this for your own secure secret key. Defaults to random secret key on every Duck launch.
SECRET_KEY: str = os.environ.get("DUCK_SECRET_KEY", DUCK_SECRET)


# Debug Mode
# Specifies whether to run the server in debug mode.
# - In debug mode (`DEBUG=True`), the DuckSight Reloader is enabled, and default Duck views are automatically registered.
# - When `DEBUG=False` (recommended for production):
#   - Default Duck views are not registered at any URL, except for `MEDIA_URL` and `STATIC_URL` if applicable.
#   - You must define and register your own URLs by adding `path` or `re_path` entries in the `urlpatterns` list in `urls.py`.
DEBUG: bool = True


# HTTPS
# Specifies whether to enable HTTPS for the server.
# - When `ENABLE_HTTPS=True`, HTTPS is enabled on the specified port.
# - Ensure you have valid SSL certificates configured for secure communication.
ENABLE_HTTPS: bool = False


# Force HTTPS
# Enforces HTTPS by redirecting unencrypted HTTP traffic to HTTPS.
# - When `FORCE_HTTPS=True`, all HTTP requests will be redirected to HTTPS.
FORCE_HTTPS: bool = False


# Force HTTPS Bind Port
# Specifies the port for the redirection app to handle HTTP to HTTPS redirection.
# - This port will listen for unencrypted traffic and redirect it to the HTTPS-enabled app.
FORCE_HTTPS_BIND_PORT: int = 8080


# Allowed Hosts, Wildcards Allowed
ALLOWED_HOSTS: list[str] = ["*"]


# Module for urlpatterns definition.
URLPATTERNS_MODULE: str = "urls"


# Blueprints
# Blueprints are more Flask's blueprints for organizing routes.
# **Note**: The blueprint name will determine the entire route, e.g.
# For route `/home` and blueprint with name `products`, the final route will be `/products/home`. This behavior can be disabled by setting argument `prepend_name_to_url` to False.
# The best way to maximize usage of blueprints, create subfolders within base directory and create blueprints and their related views in those subfolders for good project organization.
BLUEPRINTS: list[str] = [
    "duck.etc.apps.essentials.blueprint.MediaFiles",
    "duck.etc.apps.essentials.blueprint.StaticFiles",
    "duck.etc.apps.react_frontend.blueprint.ReactFrontend",
]


# Asynchronous Request Handling

# Determines whether to use asynchronous request handling.
# If set to False, the framework defaults to multithreaded request handling.
# Example: ASYNC_HANDLING=True enables async handling; False uses threads.
ASYNC_HANDLING: bool = True


# DJANGO INTEGRATION
# Whether to use Django for Backend
# This will make Duck server act as Proxy for Django
USE_DJANGO: bool = False


# Django Server Port
# This is the port where django server will be started on
DJANGO_BIND_PORT: int = 9999


# URLS to  be parsed straight to django
# This is only useful for urls that were registered with django but not with duck .e.g /admin
# These urls don't pass through the processing middlewares (responsible for detecting errors like Not found.)
# Add a url if the urlpattern was defined only directly in the Django side.
# **Note:** To avoid conflicts, only make sure that the url pattern definition is only in Django (Duck doesnt know of any urlpattern matching this).
# Regex urls are allowed
DJANGO_SIDE_URLS: list[str] = [
    "/admin.*",
]


# Duck Explicit URLs
# These are urls you want to be explicitly handled by Duck if USE_DJANGO=True
# By default, if USE_DJANGO=True, all requests will be proxied to Django first to obtain a response
# Even if you define urlpatterns within the Duck side, those urlpatterns will be registered at django endpoint as well.
# This option flags all requests matching urls defined here to avoid all that effort of being first sent to Django server to produce a response, but
# rather be handled directly (in short, prefer Duck over Django).
# This is very useful for reducing latency for requests that do not rely operations that need Django. (e.g staticfiles handling, mediafiles handling, etc)
# These URLs are considered more over DJANGO_SIDE_URLS if same url is defined both here and in DJANGO_SIDE_URLS
DUCK_EXPLICIT_URLS: list = [
    "/duck-static.*",
    "/static.*",
    "/media.*",
]


# Template Dirs
# Global Directories to lookup templates
TEMPLATE_DIRS: list[str | pathlib.Path] = [pathlib.Path("templates/").resolve()]


# List of all middlewares as strings in form "middleware.MiddlewareClass"
# WARNING: The middlewares should be arranged in order at this point.
MIDDLEWARES: list[str] = middlewares
