"""
File containing settings for Duck application.
"""
# yapf: disable
import os
import json
import pathlib

from duck.html.components.utils.include import (
    BUILTIN_COMPONENTS,
    components_include,
)
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


# Support HTTP/2 Protocol
SUPPORT_HTTP_2: bool = True


#  HTTP/2 Receive timeout
HTTP_2_RECEIVE_TIMEOUT: float | int = 0.5 # Fast response time


# Enable or disable autoreload for the server on file changes.
# Autoreload is disabled on devices such as phones to optimize performance.
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
# This wsgi is responsible for processing requests, generating response and sending it to the client unlike other
# WSGI which only generate response but does'nt send it to client.
WSGI: str = "duck.http.core.wsgi.WSGI"


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


# Silent, No Logs
# Whether to start application with no console logs.
# **Note**: If LOG_TO_FILE is enabled, logs will keep on being logged to file instead.
SILENT: bool = False


# Django Silent, No Logs
# Whether to disable Django console logs also.
DJANGO_SILENT: bool = False


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


# Request Class Configuration
# Specifies the class to be used for parsing incoming requests.
# - The class should be derived from `Duck HttpRequest` to ensure proper request handling.
REQUEST_CLASS: str = "duck.http.request.HttpRequest"


# Request Handling Task Executor
# This is the class for executing request handling threads or coroutines.
# The method 'execute' will be called every time a request has been accepted ready to be handled.
# WARNING: This is very critical in executing all requests handling.
REQUEST_HANDLING_TASK_EXECUTOR: str = "duck.http.core.httpd.task_executor.RequestHandlingExecutor"


# Request Handling Task Executor keyword arguments
# These are keyword arguments to parse to the request handling task executor.
# Do help on the executor to see supported keyword arguments.
# Predefined async executors:
#   "duck.http.core.httpd.task_executor.trio_execute"
#   "duck.http.core.httpd.task_executor.curio_execute"
REQUEST_HANDLING_TASK_EXECUTOR_KWARGS: dict = {
    "async_executor": None,
    "thread_executor": None,
}

# Asynchronous Request Handling

# Determines whether to use asynchronous request handling.
# If set to False, the framework defaults to multithreaded request handling.
# Example: ASYNC_HANDLING=True enables async handling; False uses threads.
ASYNC_HANDLING: bool = True


# Server Buffer
# Size of the buffer used to receive data chunks per request.
# Defines the maximum size (in bytes) of each chunk of data received by the server.
# Default value is set to 1024 bytes (1 KB). Adjust based on expected request sizes.
SERVER_BUFFER: int = 1024


# Server Polling Interval
# The time (in seconds) for the server to sleep while waiting for incoming requests.
# A smaller value (e.g., 0.1) will make the server check for requests more frequently,
# while a larger value (e.g., 2) reduces the frequency of checks, saving CPU resources.
# Can be specified as either an integer or a floating-point number.
SERVER_POLL: int | float = .05 # Fast responses


# Keep-Alive Timeout
# Specifies the time (in seconds) to wait for the next request from the same client.
# - This setting is only applicable when `CONNECTION_MODE='keep-alive'`.
# - Note: This is distinct from `REQUEST_TIMEOUT`, which defines the wait time for the initial client request.
KEEP_ALIVE_TIMEOUT: int | float = 1


# Request Timeout
# Specifies the time (in seconds) to wait for a client request after connecting to the Duck Server.
# - A lower timeout might result in incomplete client requests if the client takes too long to send data.
# - However, a lower timeout can also reduce latency, improving the speed of sending data back to the client or minimizing waiting time for full client requests.
REQUEST_TIMEOUT: int | float = 0.5  # Optimized for fast request processing


# Requests Backlog
# The maximum number of pending requests allowed in the backlog.
REQUESTS_BACKLOG: int = 200


# Mode for connection
# If keep-alive, the client requests will be handled using keep-alive if Header connection is set to the respective connection mode.
CONNECTION_MODE: str = "close"


# Response Content Compression
# Whether to compress response content
# Note: If a backend server like Django is used, then content compression will depend on that server.
CONTENT_COMPRESSION: dict[str] = {
    "encoding": "gzip",
    "min_size": 1024,  # files more than 1KB
    "max_size": 2048,  # files not more than 2KB
    "level": 5,
    "vary_on": True,  # Whether to include Vary header in response
    "mimetypes": [
        "text/html",
        "text/css",
        "application/javascript",
        "application/json",
        "application/xml",
        "application/xhtml+xml",
        "application/rss+xml",
        "application/atom+xml",
    ],  # avoid compressing already compressed files like images
}


# Enable Content Compression
# Specifies whether to enable content compression for responses.
ENABLE_CONTENT_COMPRESSION: bool = True


# Proxy Handler
# This class handles proxying requests between the client and a Django server.
# To create a custom proxy handler, subclass `HttpProxyHandler`.
# Override the following methods for custom behavior:
# - `modify_client_request_headers`: Alter client request headers before forwarding them to the remote server.
# - `modify_client_response_headers`: Modify response headers before sending the response back to the client.
# **Caution**: Overriding these methods can lead to unexpected behavior if not handled properly.
PROXY_HANDLER: str = "duck.http.core.proxyhandler.HttpProxyHandler"


# Timeout to establish a connection with the remote proxy server (e.g., Django).
# A value of 1 second is typically used for fast responses. 
# Consider increasing if connection time to the server is high.
PROXY_CONNECT_TIMEOUT = 1  # Timeout in seconds for establishing the connection


# Timeout to wait for data from the remote proxy server.
# This value should balance between waiting for data and not blocking indefinitely.
# Increase if network latency or server load is high.
PROXY_READ_TIMEOUT = 3  # Timeout in seconds for reading data


# The amount of data to stream at once from the remote proxy server.
# 4096 bytes (4 KB) is a reasonable default chunk size for streaming,
# but can be adjusted based on specific requirements.
PROXY_STREAM_CHUNK_SIZE = 4096


# DJANGO INTEGRATION
# Whether to use Django for Backend
# This will make Duck server act as Proxy for Django
USE_DJANGO: bool = False


# Django Server Port
# This is the port where django server will be started on
DJANGO_BIND_PORT: int = 9999


# Django Server Wait Time
# Time in seconds to wait before checking if the Django server is up and running.
# This variable is used to periodically verify the server's status during the initial startup or maintenance routines, ensuring that the server is ready to handle incoming requests.
DJANGO_SERVER_WAIT_TIME: str = 2


# These commands will be run before Django server startup if USE_DJANGO is set to True.
# Leave empty if you don't want to run any commands
DJANGO_COMMANDS_ON_STARTUP: list[str] = [
    # "makemigrations",
    # "migrate",
    # "collectstatic --noinput",
]


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
] # Optimized fast mode, remove ".*" for normal optimum flow'


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



# Whether Django registered urls must skip Duck middleware checks
# These middlewares are those set in settings.py, not processing middlewares (responsible for processing request further).
# This adds an extra layer of security for urlpatterns defined in Django only if set to False.
DJANGO_SIDE_URLS_SKIP_MIDDLEWARES: bool = False


# DuckApp will use this as the ID domain for Django to recognize/accept our requests (if applicable).
# Will be used also to validate private connection between Duck and Django.
DJANGO_SHARED_SECRET_DOMAIN: str = os.environ.get(
    "DJANGO_SHARED_SECRET_DOMAIN", SECRET_DOMAIN)


# Template Dirs
# Global Directories to lookup templates
TEMPLATE_DIRS: list[str | pathlib.Path] = [pathlib.Path("templates/").resolve()]


# Module which contains Custom Template Tags or Filters
# Set to '' to disable custom tags or filters
# Example:
# # templatetags.py
# from duck.template.templatetags import TemplateTag, TemplateFilter
#
# def mytag(arg1):
# 	# do some stuff here
# 	return "some data"
#
# def myfilter(data):
# 	# do some stuff here
# 	return data
#
# def myblocktag(content):
#       # do something
#       return content
#
# TEMPLATETAGS = [
# 	TemplateTag("name_here", mytag, takes_context=False), # takes_context defaults to False
# 	TemplateFilter("name_here", myfilter),
#     BlockTemplateTag("name_here", myblocktag)
# ]
#
# **Note**: If you would like to use Duck tags or filters in template rendered with Django (Templates rendered by using django.shortcuts.render), insert the following at the beginning of the template:
# 	{% load ducktags %}
#
# There is no need for doing this if your template is being rendered from Duck internal functions like render or classes like TemplateResponse,
# Only use this for django sided templates that has nothing to do with Duck.
TEMPLATETAGS_MODULE: str = ""


# Html Components
# These are template tags which can be used to dynamically create HTML elements
# Example Usage:
# Jinja2 Template
# {{ Button(
#     properties={
#         "value": "Hello world",
#          "id": "btn"
#      },
#      style={
#          "background-color": "red",
#           "color": "white",
#        },
#        optional_argument="Some value",
#      )
# }}
# 
# Django Template
# {% Button %}
#     properties={
#         "id": "btn",
#         "value": "Hello world"
#      },
#      style={
#           "background-color": "blue",
#            "color": "white"
#       },
#       optional_argument="Some value"
# {% endButton %}


# You can create your custom HtmlComponent by subclassing the component from duck.html.components.InnerHtmlComponent or NoInnerHtmlComponent.
# Do help on how these two classes work
# 
# Example:
# from duck.html.components import InnerHtmlComponent
# 
# class CustomButton(InnerHtmlComponent):
#    """
#    CustomHTML Button component.
#    """
#    def get_element(self):
#        return "button"
#    
#    def on_create(self):
#         # Modify or update style and properties
#         
#         # update style here using setdefaults
#         # Note: there is an "s" for setdefaults for dictionary instead of key and value
#         self.style.setdefaults({
#             "color": "white",
#             "background-color": "red",
#         })
#         
#         if "onclick" self.kwargs:
#             self.properties.setdefault("onclick", self.kwargs.get("onclick")) # you can optionally modify props and style absolutely by using update or indexing

HTML_COMPONENTS: dict[str, str] = {
    "Button": "duck.html.components.button.Button", # example
    **components_include(BUILTIN_COMPONENTS),
}

# Enable Html Components
# Enable html components usage in templates.
ENABLE_HTML_COMPONENTS: bool = True


# Frontend Integration
# Currently, only React is supported.
# Use React within your template using the following template tag:
#    {% react_frontend %}
#        Your JSX Code here
#    {% endreact_frontend %}
#
FRONTEND: dict[str, dict] = {
    "REACT": {
        # URLs or filepaths for loading React, ReactDOM, and Babel scripts (Javascript only).
        # **Note**: Babel script is required.
        "scripts": [
            "https://unpkg.com/react@17/umd/react.development.js",
            "https://unpkg.com/react-dom@17/umd/react-dom.development.js",
            "https://unpkg.com/@babel/standalone/babel.min.js"
        ],
        # Root URL for the React application, this serves the jsx code in between "react_fronted" template tag.
        "root_url": "/react/serve",
        "scripts_url": "/scripts", # URL for serving the above scripts. Final Route = root_url + scripts_url.
    }
}

# Custom Templates
# These are custom templates you might want to use for different various status codes
# This maps status codes to callables which are responsible for generating new responses.
# The following are the arguments parsed to custom template callables:
#     current_response: The HTTP response object containing the preprocessed response.
#     request (optional):
#         The corresponding request, can be None if the response was generated at a lower level before
#          the request data was processed.
# **Note:** This is only effective in PRODUCTION (not in DEBUG mode).
CUSTOM_TEMPLATES: dict = {}


# Default Request Headers (loaded from JSON files)
# These headers are added to every response by default.
# The headers are loaded from the JSON file specified in the path.
with open(os.path.join(duck_storage, "etc/headers/default.json")) as fd:
    SECURITY_HEADERS: dict = json.load(fd)


# Default Request Headers for HTTPS (loaded from JSON files)
with open(os.path.join(duck_storage, "etc/headers/default_ssl.json")) as fd:
    SSL_SECURITY_HEADERS: dict = json.load(fd)


# Extra Headers
EXTRA_HEADERS: dict = {}


# CORS Headers
CORS_HEADERS: dict = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Max-Age": "86400",
}


# List of all middlewares as strings in form "middleware.MiddlewareClass"
# WARNING: The middlewares should be arranged in order at this point.
MIDDLEWARES: list[str] = middlewares


# Middleware Failure default behavior.
# This setting determines the action when a Request fails to meet the conditions to pass through the middleware.
# It defaults to 'block' to block all requests that fail to satisfy any middleware conditions.
MIDDLEWARE_FAILURE_BEHAVIOR: str = "block"


#  Request Normalizers
# These Normalizers accept a Request object as an argument and return the Request object with normalized attributes.
NORMALIZERS: list[str] = normalizers


# Ignore Normalization Errors
# Whether to ignore errors raised from trying to normalize request.
IGNORE_NORMALIZATION_ERRORS: bool = True


# Headers Security Policy
# This Policy creates Security Headers for every response, The headers that will be added are either HTTP_DEFAULT_HEADERS or HTTPS_DEFAULT_HEADERS
# SECURITY WARNING: If both HTTP_DEFAULT_HEADERS and HTTPS_DEFAULT_HEADERS are empty, this setting will result in nothing
ENABLE_HEADERS_SECURITY_POLICY: bool = True


# SESSION SETTINGS
# This class is used for storing session data. Available cache classes include:
# - duck.utils.caching.InMemoryCache
# - duck.utils.caching.KeyAsFolderCache
# - duck.utils.caching.DynamicFileCache
#
# For detailed information on how these classes work and their benefits, use the help function.
# You can also use a custom cache class, but ensure it implements the following methods: set, get, delete, clear, save.
SESSION_STORAGE: str = "duck.utils.caching.KeyAsFolderCache"


# Session Engine
# The session engine to use for managing user sessions.
# This engine interacts with session storage to perform session operations.
#
# **Note:** 
# - Avoid overriding this directly if you primarily intend to customize session storage. 
# - It's generally preferable to override the session storage mechanism instead.
# - This engine will *not* be automatically synchronized with Django if `USE_DJANGO=True`. 
#   To integrate with Django, you'll need to create a custom Django session backend.
SESSION_ENGINE = "duck.http.session.engine" 


# Session Directory
# Specifies the directory to store session data.
# - If using database session storage, this can be set to `None`.
# - The directory will be automatically created if it does not exist.
SESSION_DIR: str = BASE_DIR / "assets/.cache"


# Session Cookie Name
# The name of the cookie that stores the session ID in the client's request.
SESSION_COOKIE_NAME: str = "session_id"


# Session Duration
# The duration (in seconds) for which a session will remain active.
# Default is set to 7 days (604800 seconds).
SESSION_COOKIE_AGE: int | float = 604800  # 7 days


# Session Cookie Path
SESSION_COOKIE_PATH: str = "/"


# Session Cookie Domain
SESSION_COOKIE_DOMAIN: str = None


# Session Expire At Browser Close
# Whether for sessions to expire at browser close
SESSION_EXPIRE_AT_BROWSER_CLOSE: bool = False


# Session Cookie Secure
# Whether session cookie should be accessed only on https
SESSION_COOKIE_SECURE: bool = False


# Session Cookie HttpOnly
# Whether session cookie should be accessible via http only (javascript not allowed)
SESSION_COOKIE_HTTPONLY: bool = True


# Session Cookie SameSite
SESSION_COOKIE_SAMESITE: str = "Lax"


# Csrf Secret Length
# The length for the csrf secret key.
CSRF_SECRET_LENGTH: int = 32


# Csrf Token Length
CSRF_TOKEN_LENGTH: int = 64


# Csrf Session Key
# The name for the csrf secret in request sessions.
CSRF_SESSION_KEY: str = "_csrftoken"


# CSRF Cookie Name
# The name of the cookie that holds the CSRF token for POST requests.
CSRF_COOKIE_NAME: str = "csrftoken"


# CSRF Header Name
# The header name sent to the client when a new CSRF token is generated for that client.
CSRF_HEADER_NAME: str = "X-CSRF-Token"


# Lifetime of the CSRF cookie in seconds (default is 7 days)
CSRF_COOKIE_AGE: int | float = 604800


# Path for which the CSRF cookie is valid (default is "/")
CSRF_COOKIE_PATH: str = "/"


# Domain for which the CSRF cookie is valid (default is None, meaning the domain of the current request)
CSRF_COOKIE_DOMAIN: str = None


# Whether to send the CSRF cookie only over HTTPS connections (default is False)
CSRF_COOKIE_SECURE: bool = False


# Whether the CSRF cookie should be HttpOnly (default is True, which prevents JavaScript access)
CSRF_COOKIE_HTTPONLY: bool = True


# SameSite attribute for CSRF cookie. Can be 'Strict', 'Lax', or 'None' (default is 'Lax')
CSRF_COOKIE_SAMESITE: str = "Lax"


# Whether to store the CSRF token in the session instead of in a cookie (default is False)
CSRF_USE_SESSIONS: bool = False


# STATIC FILES HANDLING

# These are global static directories to lookup for static files when
# `collectstatic` command is used
GLOBAL_STATIC_DIRS: list[str] = [BASE_DIR / "static"]


# The root directory for storing static files.
# Auto created if it does'nt exist
STATIC_ROOT: str = BASE_DIR / "assets/staticfiles"


# The URL to use for serving static files.
STATIC_URL: str = "static/"


# MEDIA FILES HANDLING

# Media Root
# This is where the media files will reside in.
# Auto created if it does'nt exist
MEDIA_ROOT: str = BASE_DIR / "assets/media"


# Media Url
# This is the url for serving media files
MEDIA_URL: str = "media/"


# File Upload Handler Configuration
# Specifies the handler used to save uploaded files.
# - Default is `PersistentFileUpload`, which saves uploaded files in local storage.
# Other alternative is TemporaryFileUpload
FILE_UPLOAD_HANDLER: str = "duck.http.fileuploads.handlers.PersistentFileUpload"


# File Upload Directory Configuration
# Specifies the directory where uploaded files will be stored.
# - Required if `PersistentFileUpload` is used as the `FILE_UPLOAD_HANDLER`.
# - The directory will be automatically created if it doesn't already exist.
FILE_UPLOAD_DIR: str = BASE_DIR / "assets/uploads"


# LOGGING SETTINGS
# Logging Directory
# This is the directory to place all logs
LOGGING_DIR: str = BASE_DIR / "assets/.logs"


# Log File Format
# Format for log files with date and time, safe for Windows filenames
LOG_FILE_FORMAT: str = "{year}-{month:02d}-{day:02d}_{hours:02d}-{minutes:02d}-{seconds:02d}"


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
    #"duck.automation.SampleAutomation": {
    #   "trigger": "duck.automation.trigger.NoTrigger",
    # }
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


# SYSTEMD CONFIGURATION
# systemd is a system and service manager used in Linux distributions.
# It controls the starting, stopping, and monitoring of services, making 
# it ideal for managing background processes like web servers.
#
# For the Duck Web Server, using systemd ensures that the server can:
# - Start automatically on boot
# - Be managed easily through standard commands (`start`, `stop`, `restart`)
# - Restart automatically if it crashes or stops unexpectedly
# - Run in the background as a service, freeing up the terminal

# Systemd Execution Command
# Specifies the command that will be executed when the systemd service starts.
# In this case, it runs the Duck web server on port 80, binding it to all available interfaces.
SYSTEMD_EXEC_COMMAND: str = "python -m duck runserver -p 80 -a 0.0.0.0 -d localhost"


# Systemd Service Name
# Defines the name of the systemd service unit file. 
# This will be used when managing the service with systemctl (e.g., starting, stopping, enabling).
SYSTEMD_SERVICE_NAME: str = "duck-service.service"


# Systemd Environment
# Provides the environment variables that should be set for the service.
# The environment is typically populated with the current system environment variables (os.environ).
SYSTEMD_ENVIRONMENT: dict = os.environ


# Systemd Restart Policy
# Specifies the restart behavior for the service.
# "always" ensures that the service will be restarted automatically if it fails or stops unexpectedly.
SYSTEMD_RESTART: str = "always"


# Systemd Service Directory
# Indicates the directory where the systemd service unit file will be stored.
# Typically, service unit files are placed in /etc/systemd/system/ for system-wide services.
SYSTEMD_SERVICE_DIR: str = "/etc/systemd/system/"
