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
from duck.storage import duck_storage, BaseDir


# Base directory where the Duck application is running from
BASE_DIR: str | pathlib.Path = BaseDir()


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
ASYNC_HANDLING: bool = False


# DJANGO INTEGRATION
# Whether to use Django for Backend
# This will make Duck server act as Proxy for Django
USE_DJANGO: bool = False


# Django Server Port
# This is the port where django server will be started on
DJANGO_BIND_PORT: int = 9999


# Duck Explicit URLs  
# Defines URLs that Duck should handle directly when USE_DJANGO=True.  
# By default, if DUCK_EXPLICIT_URLS is empty, all requests are processed by Django,  
# even if Duck has its own urlpatterns. Duck’s urlpatterns are effectively duplicated  
# on the Django side, meaning Django handles all matching requests first.  

# This setting allows specific URLs to bypass Django and be handled by Duck directly,  
# but only if no matching URL pattern exists in DJANGO_SIDE_URLS. If pattern in DJANGO_SIDE_URLS,  
# Django still takes precedence.  

# Use this to optimize performance by letting Duck handle requests that don’t require Django,  
# such as static/media file serving.  
DUCK_EXPLICIT_URLS: list = [
    ".*"
] # Optimized fast mode, remove .* for normal optimum flow (processing Duck urls on Django side).


# URLS to  be parsed straight to django
# This is only useful for urls that were registered with django but not with duck .e.g /admin
# These urls don't pass through the processing middlewares (responsible for detecting errors like Not found.)
# Add a url if the urlpattern was defined only directly in the Django side.
# **Note:** To avoid conflicts, only make sure that the url pattern definition is only in Django (Duck doesnt know of any urlpattern matching this).
# Eg. "/admin.*", Regex urls are allowed

# Note: If a URL is only defined in Django and is not listed in DJANGO_SIDE_URLS,  
# it will still result in a 404 response when accessed through Duck.

DJANGO_SIDE_URLS: list[str] = [
    "/admin.*",
    "/x-static.*"
]


# Template Dirs
# Global Directories to lookup templates
TEMPLATE_DIRS: list[str | pathlib.Path] = [pathlib.Path("templates/").resolve()]


# List of all middlewares as strings in form "middleware.MiddlewareClass"
# WARNING: The middlewares should be arranged in order at this point.
MIDDLEWARES: list[str] = middlewares


# IMPORTANT DIRS
# These directories is a must to be defined as leaving these will use default Duck internal directories 

# These are global static directories to lookup for static files when
# `collectstatic` command is used
GLOBAL_STATIC_DIRS: list[str] = [BASE_DIR / "static"]


# The root directory for storing static files.
# Auto created if it does'nt exist
STATIC_ROOT: str = BASE_DIR / "assets/staticfiles"


# MEDIA FILES HANDLING

# Media Root
# This is where the media files will reside in.
# Auto created if it does'nt exist
MEDIA_ROOT: str = BASE_DIR / "assets/media"


# File Upload Directory Configuration
# Specifies the directory where uploaded files will be stored.
# - Required if `PersistentFileUpload` is used as the `FILE_UPLOAD_HANDLER`.
# - The directory will be automatically created if it doesn't already exist.
FILE_UPLOAD_DIR: str = BASE_DIR / "assets/uploads"


# LOGGING SETTINGS
# Logging Directory
# This is the directory to place all logs
LOGGING_DIR: str = BASE_DIR / "assets/.logs"


# SSL CERTIFICATE SETTINGS

# SSL Certificate Location
SSL_CERTFILE_LOCATION: str = BASE_DIR / "etc/ssl/server.crt"


# SSL Private Key Location
# SECURITY WARNING: Keep this safe to avoid security bridges
SSL_PRIVATE_KEY_LOCATION: str = BASE_DIR / "etc/ssl/server.key"
