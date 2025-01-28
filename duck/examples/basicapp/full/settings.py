"""
File containing settings for Duck application.
"""

import json
import os
import pathlib

from duck.etc.middlewares import middlewares
from duck.etc.normalizers import normalizers
from duck.secrets import DUCK_SECRET, SECRET_DOMAIN
from duck.storage import duck_storage

# Base directory where the Duck application is running from
BASE_DIR: str | pathlib.Path = pathlib.Path(".").resolve()

# SECURITY WARNING: keep the secret key used in production secret! Will be used also to validate private connection
# between Duck app and Django
SECRET_KEY: str = os.environ.get("DUCK_SECRET_KEY", DUCK_SECRET)

# Debug Mode
# Specifies whether to run the server in debug mode.
# - In debug mode (`DEBUG=True`), the DuckSight Reloader is enabled, and default Duck views are automatically registered.
# - When `DEBUG=False` (recommended for production):
#   - Default Duck views are not registered at any URL, except for `MEDIA_URL` and `STATIC_URL` if applicable.
#   - You must define and register your own URLs by adding `path` or `re_path` entries in the `urlpatterns` list in `urls.py`.
DEBUG: bool = True

# Whether to autoreload server on file changes
AUTO_RELOAD: bool = True

# Auto reload poll
# Time in seconds to delay before listening for file changes.
AUTO_RELOAD_POLL: float = 1

# Files to watch for when autoreload
AUTO_RELOAD_WATCH_FILES = ["*.py"]

# Path to the python interpreter or just the interpreter executable path
PYTHON_PATH: str = "python"

# Web Server Gateway Interface (WSGI) to use within Duck.
# **Caution**: Changing WSGI may result in unexpected behavior for logging if not handled correctly.
WSGI: str = "duck.http.wsgi.WSGI"

# HTTPS
# Specifies whether to enable HTTPS for the server.
# - When `ENABLE_HTTPS=True`, HTTPS is enabled on the specified port.
# - Ensure you have valid SSL certificates configured for secure communication.
ENABLE_HTTPS: bool = True

# Force HTTPS
# Enforces HTTPS by redirecting unencrypted HTTP traffic to HTTPS.
# - When `FORCE_HTTPS=True`, all HTTP requests will be redirected to HTTPS.
FORCE_HTTPS: bool = True

# Force HTTPS Bind Port
# Specifies the port for the redirection app to handle HTTP to HTTPS redirection.
# - This port will listen for unencrypted traffic and redirect it to the HTTPS-enabled app.
FORCE_HTTPS_BIND_PORT: int = 8000

# Allowed Hosts, Wildcards Allowed
ALLOWED_HOSTS: list[str] = ["*"]

# Request Class Configuration
# Specifies the class to be used for parsing incoming requests.
# - The class should be derived from `Duck HttpRequest` to ensure proper request handling.
REQUEST_CLASS: str = "duck.http.request.HttpRequest"

# Module for urlpatterns definition.
URLPATTERNS_MODULE: str = "urls"

# Route Blueprints
# Route blueprints are more Flask's blueprints for organizing routes.
# **Note**: The blueprint name will determine the entire route, e.g.
# For route `/home` and blueprint with name `products`, the final route will be `/products/home`
# The best way to maximise usage of blueprints, create subfolders within base directory and create blueprints and their related views in those subfolders for good project organization.
ROUTE_BLUEPRINTS: list[str] = [
    # your blueprints here, e.g.
    # blueprints.SampleBlueprint
]

# Keep-Alive Timeout Configuration
# Specifies the time (in seconds) to wait for the next request from the same client.
# - This setting is only applicable when `CONNECTION_MODE='keep-alive'`.
# - Note: This is distinct from `REQUEST_TIMEOUT`, which defines the wait time for the initial client request.
KEEP_ALIVE_TIMEOUT: int | float = 1

# Keep-Alive Timeout
# Specifies the time (in seconds) to wait for the next request from the same client.
# - This setting is only applicable when `CONNECTION_MODE='keep-alive'`.
# - Note: This is distinct from `REQUEST_TIMEOUT`, which defines the wait time for the initial client request.
KEEP_ALIVE_TIMEOUT: int | float = 1

# Request Timeout
# Specifies the time (in seconds) to wait for a client request after connecting to the Duck Server.
# - A lower timeout might result in incomplete client requests if the client takes too long to send data.
# - However, a lower timeout can also reduce latency, improving the speed of sending data back to the client or minimizing waiting time for full client requests.
REQUEST_TIMEOUT: int | float = 0.1  # Optimized for fast request processing

# Proxy Handler
# This class handles proxying requests between the client and a Django server.
# To create a custom proxy handler, subclass `HttpProxyHandler`.
# Override the following methods for custom behavior:
# - `modify_client_request_headers`: Alter client request headers before forwarding them to the remote server.
# - `modify_client_response_headers`: Modify response headers before sending the response back to the client.
# **Caution**: Overriding these methods can lead to unexpected behavior if not handled properly.
PROXY_HANDLER: str = "duck.http.processing.proxyhandler.HttpProxyHandler"

# DJANGO INTEGRATION
# Whether to use Django for Backend
# This will make Duck server act as Proxy for Django
USE_DJANGO: bool = False

# Django Server Port
# This is the port where django server will be started on
DJANGO_BIND_PORT: int = 10000

# Django Server Wait Time
# Time in seconds to wait before checking if the Django server is up and running.
# This variable is used to periodically verify the server's status during the initial startup or maintenance routines, ensuring that the server is ready to handle incoming requests.
DJANGO_SERVER_WAIT_TIME: str = 5

# These commands will be run before Django server startup if USE_DJANGO is set to True.
# Leave empty if you don't want to run any commands
DJANGO_COMMANDS_ON_STARTUP: list[str] = [
    "makemigrations",
    "migrate",
    "collectstatic --noinput",
]

# URLS to  be parsed right to django
# This is only useful for urls that were registered with django but not with duck .e.g /admin
# Regex urls are allowed
DJANGO_REGISTERED_URLS: list[str] = [
    "/admin",
]

# DuckApp will use this as the ID domain for Django to recognize/accept our Requests (if applicable).
DJANGO_SHARED_SECRET_DOMAIN: str = os.environ.get(
    "DJANGO_SHARED_SECRET_DOMAIN", SECRET_DOMAIN)

# Whether to support Django Templating.
# This is useful if you want to use DjangoTemplateResponse and don't want to use Django for the backend.
# Note: Django Templating is supported by default if USE_DJANGO is set to True. # This will do a small hack to achieve this.
SUPPORT_DJANGO_TEMPLATING: bool = True

# Directory to lookup templates
# Duck uses single template directory to avoid inaccuraces like retreiving wrong template which might available in many template directories.
TEMPLATE_DIR: str | pathlib.Path = pathlib.Path("templates/").resolve()

# Module which contains Custom Template Tags or Filters
# Set to '' to disable custom tags or filters
# Example:
# # tags.py
# from duck.template import TemplateTag, TemplateFilter
#
# def mytag(arg1):
# 	# do some stuff here
# 	return "some data"
#
# def myfilter(data):
# 	# do some stuff here
# 	return data
#
# TAGS = [
# 	TemplateTag("name_here", mytag, takes_context=False) # takes_context defaults to False
# ]
#
# FILTERS = [
# 	TemplateFilter("name_here", myfilter)
# ]
TEMPLATE_TAGS_FILTERS_MODULE: str = ""

# Html Components to use in Templates
# These are template tags which can be used to dynamically create HTML elements
# Example:
# Jinja2 Template
# {{ Button(
# 	style={
# 		"background-color": "red",
# 		"color": "white",
# 		},
# 	properties={
# 		"value": "Hello world",
# 		"id": "btn"
# 		},
# 	)
# }}
#
# Django Template
# {% Button properties='{"id": "btn", "value": "Hello world"}' style='{"background-color": "blue", "color": "white"}' %}
#
# **Note**: In django please make sure the tag is oneline and keyword arguments are quoted as strings e.g. properties='{"key": "value"}'
ENABLE_HTML_COMPONENTS: bool = True

# Enabled Html Components
# These are mapping of Html Component Name to the Html Component class
# You can create your custom HtmlComponent by subclassing the component from duck.html.components.InnerHtmlComponent or NoInnerHtmlComponent.

# Do help on how these two classes work
# Example:
# class Button(InnerHtmlComponent):
#    """
#    HTML Button component.
#    """
#    def __init__(self, properties: dict[str, str]={}, style: dict[str, str]={}):
#        """
#        Initialize the FlatButton component.
#        """
#        btn_style = {
#            "padding": "10px 20px",
#            "cursor": "pointer",
#            "transition": "background-color 0.3s ease",
#            "border": "none",
#        } # default style
#
#        btn_style.update(style) if style else None # update default style
#
#        super().__init__("button", properties, btn_style)

HTML_COMPONENTS: dict[str, str] = {
    "Button": "duck.html.components.button.Button",
    "FlatButton": "duck.html.components.button.FlatButton",
    "RaisedButton": "duck.html.components.button.RaisedButton",
    "Input": "duck.html.components.input.Input",
    "CSRFInput": "duck.html.components.input.CSRFInput",
    "Checkbox": "duck.html.components.checkbox.Checkbox",
    "Select": "duck.html.components.select.Select",
    "TextArea": "duck.html.components.textarea.TextArea",
}

# Default Request Headers (loaded from JSON files)
# Enable Security Headers Policy to make use of HTTP_DEFAULT_HEADERS or HTTPS_DEFAULT_HEADERS
# without ssl/http-only
# usually these are secure headers
with open(os.path.join(duck_storage, "etc/headers/default.json")) as fd:
    HTTP_DEFAULT_HEADERS: dict = json.load(fd)

# with ssl/https
# usually these are secure headers
with open(os.path.join(duck_storage, "etc/headers/default_ssl.json")) as fd:
    HTTPS_DEFAULT_HEADERS: dict = json.load(fd)

# List of all middlewares as strings in form "middleware.MiddlewareClass"
# Make sure DuckToDjangoMetaDataShareMiddleware is in MIDDLEWARES so as to
# enable good cooperation between duck and django if Django is used as backend
# WARNING: The middlewares should be arranged in order at this point
MIDDLEWARES: list[str] = middlewares

# Remove some middlewares if USE_DJANGO=True
if USE_DJANGO:
    for ignore_middleware in (
            "duck.http.middlewares.contrib.SessionMiddleware",
            "duck.http.middlewares.security.CSRFMiddleware",
    ):
        if ignore_middleware in MIDDLEWARES:
            MIDDLEWARES.remove(ignore_middleware)

# Middleware Failure default behavior.
# This setting determines the action when a Request fails to meet the conditions to pass through the middleware.
# It defaults to 'block' to block all requests that fail to satisfy any middleware conditions.
# These only applies to middlewares in settings.py not Processing middlewares
# It can be either 'block' or 'ignore'.
MIDDLEWARE_FAILURE_DEFAULT_BEHAVIOR: str = "block"

# Enable Processing Middlewares
# These middlewares handle most errors such as NotFound, BadRequestSyntax, HttpUnsupportedVersion, HttpMethodNotAllowed, and others.
# Disable this if you intend to allow all requests or need to use Duck as a proxy server.
ENABLE_PROCESSING_MIDDLEWARES: bool = True

#  Request Normalizers
# These Normalizers accept a Request object as an argument and return the Request object with normalized attributes.
NORMALIZERS: list[str] = normalizers

# Headers Security Policy
# This Policy creates Security Headers for every response, The headers that will be added are either HTTP_DEFAULT_HEADERS or HTTPS_DEFAULT_HEADERS

# SECURITY WARNING: If both HTTP_DEFAULT_HEADERS and HTTPS_DEFAULT_HEADERS are empty, this setting will result in nothing
ENABLE_HEADERS_SECURITY_POLICY: bool = True

# SESSION SETTINGS
# Notes:
#   To ensure sessions work correctly, please verify the following settings:
#   a) SessionMiddleware must be included in the MIDDLEWARE list in settings.py.
#
#   If USE_DJANGO=True:
#   a) DuckSessionMiddleware should be listed immediately after SecurityMiddleware in the Django settings MIDDLEWARE list.
#   b) DuckToDjangoMetaDataShareMiddleware should be present in the Duck settings.py, and
#      DuckToDjangoMetaDataReceiverMiddleware should be listed above DuckSessionMiddleware in the Django settings MIDDLEWARE list.

# This class is used for storing session data. Available cache classes include:
# - duck.utils.caching.InMemoryCache
# - duck.utils.caching.KeyAsFolderCache
# - duck.utils.caching.DynamicFileCache
#
# For detailed information on how these classes work and their benefits, use the help function.
# You can also use a custom cache class, but ensure it implements the following methods: set, get, delete, clear.
SESSION_STORAGE: str = "duck.utils.caching.KeyAsFolderCache"

# Session Directory
# Specifies the directory to store session data.
# - If using database session storage, this can be set to `None`.
# - The directory will be automatically created if it does not exist.
SESSION_DIR: str = os.path.join(duck_storage, ".cache")

# Session Cookie Name
# The name of the cookie that stores the session ID in the client's request.
SESSION_COOKIE_NAME: str = "session_id"

# Session Duration
# The duration (in seconds) for which a session will remain active.
# Default is set to 7 days (604800 seconds).
SESSION_COOKIE_AGE: int | float = 604800  # 7 days

# CSRF Cookie Name
# The name of the cookie that holds the CSRF token for POST requests.
CSRF_COOKIE_NAME: str = "csrfmiddlewaretoken"

# CSRF Header Name
# The header name sent to the client when a new CSRF token is generated for that client.
CSRF_HEADER_NAME: str = "X-CSRF-Token"

# STATIC FILES HANDLING

# The root directory for storing static files.
# Auto created if it does'nt exist
STATIC_ROOT: str = BASE_DIR / "staticfiles"

# The URL to use for serving static files.
STATIC_URL: str = "static/"

# This automatically serves static files whenever the URL specified by STATIC_URL is visited.
# If disabled, even duck default static files at url '/duck-static' will not be served
AUTO_SERVE_STATICFILES: bool = True

# MEDIA FILES HANDLING

# Media Root
# This is where the media files will reside in.
# Auto created if it does'nt exist
MEDIA_ROOT: str = BASE_DIR / "media"

# Media Url
# This is the url for serving media files
MEDIA_URL: str = "media/"

# Whether to auto serve media files in MEDIA_ROOT when MEDIA_URL is visited
AUTO_SERVE_MEDIAFILES: bool = True

# File Upload Handler Configuration
# Specifies the handler used to save uploaded files.
# - Default is `PersistentFileUpload`, which saves uploaded files in local storage.
FILE_UPLOAD_HANDLER: str = (
    "duck.http.fileuploads.handlers.PersistentFileUpload")

# File Upload Directory Configuration
# Specifies the directory where uploaded files will be stored.
# - Required if `PersistentFileUpload` is used as the `FILE_UPLOAD_HANDLER`.
# - The directory will be automatically created if it doesn't already exist.
FILE_UPLOAD_DIR: str = BASE_DIR / "uploads"

# LOGGING SETTINGS
# Logging Directory
# This is the directory to place all logs
LOGGING_DIR: str = BASE_DIR / ".logs"

# Log File Format
# Format to use for all log files
LOG_FILE_FORMAT: str = "{day}-{month}-{year} {hours}-{minutes}-{seconds}"

# Log to File
# Specifies whether to save logs to files or only print them to the console.
# - When `LOG_TO_FILE=True`, logs will be stored in log files. Otherwise, logs will only be printed to the console.
LOG_TO_FILE: bool = True

# Verbose Logging
# Enables detailed logging for exceptions that cause internal server errors.
# - If `DEBUG=True`, verbose logging is enabled by default to capture additional information.
VERBOSE_LOGGING: bool = True

# AUTOMATION SETTINGS
# Automations you would like to run when the application is running.
# This is a mapping of Automation objects as a string to a dictionary with only one allowed key, ie. `trigger`.
# The key `trigger` can be either a class or an object.
# Do help on duck.automations for more info.
# Note: Preparing Automation environment may make the application startup a bit slower.
AUTOMATIONS: dict[str, dict[str, str]] = {
    "duck.automation.SampleAutomation": {
        "trigger": "duck.automation.trigger.NoTrigger",
    }
}

# Automation Dispatcher Configuration
# Specifies the class responsible for dispatching automations.
# - You can use a custom dispatcher by subclassing the `AutomationDispatcher` class and implementing the `listen` method.
AUTOMATION_DISPATCHER: str = "duck.automation.dispatcher.DispatcherV1"

# Run Automations Configuration
# Specifies whether to execute automations when the main application is deployed.
# - When `RUN_AUTOMATIONS=True`, automations will run automatically during deployment.
RUN_AUTOMATIONS: bool = True

# SSL CERTIFICATE SETTINGS

# SSL Certificate Location
SSL_CERTFILE_LOCATION: str = os.path.join(duck_storage, "etc/ssl/server.crt")

# The location of the SSL Certificate Signing Request (CSR).
SSL_CSR_LOCATION: str = os.path.join(duck_storage, "etc/ssl/server.csr")

# SSL Private Key Location
# SECURITY WARNING: Keep this safe to avoid security bridges
SSL_PRIVATE_KEY_LOCATION: str = os.path.join(duck_storage,
                                             "etc/ssl/server.key")

# SSL CERTIFICATE ACQUISITION

# Domain name for the server. Replace with fully-qualified domain name (FQDN)
SERVER_DOMAIN: str = ""

# Server country as Two-Letter country code as per ISO 3166-1 alpha-2 code eg US or ZW
SERVER_COUNTRY: str = ""  # .e.g ZW

# Server state or province e.g. California
SERVER_STATE: str = ""

# Server locality. Replace with the locality name (city, town, etc.) e.g. Harare
SERVER_LOCALITY: str = ""

# Server Organization. Replace with your legally registered organization name
SERVER_ORGANIZATION: str = ""

# Server Organization Unit. Replace with your legally registered organization unit
SERVER_ORGANIZATION_UNIT: str = ""
