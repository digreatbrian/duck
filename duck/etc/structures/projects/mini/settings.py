"""
File containing mini settings for Duck application.
"""

import os
import pathlib

from duck.etc.middlewares import middlewares
from duck.etc.normalizers import normalizers
from duck.secrets import DUCK_SECRET

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

# Web Server Gateway Interface (WSGI) to use within Duck.
# **Caution**: Changing WSGI may result in unexpected behavior for logging if not handled correctly.
WSGI: str = "duck.http.wsgi.WSGI"

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

# Route Blueprints
# Route blueprints are more Flask's blueprints for organizing routes.
# **Note**: The blueprint name will determine the entire route, e.g.
# For route `/home` and blueprint with name `products`, the final route will be `/products/home`
# The best way to maximise usage of blueprints, create subfolders within base directory and create blueprints and their related views in those subfolders for good project organization.
ROUTE_BLUEPRINTS: list[str] = [
    # your blueprints here, e.g.
    # blueprints.SampleBlueprint
]

# DJANGO INTEGRATION
# Whether to use Django for Backend
# This will make Duck server act as Proxy for Django
USE_DJANGO: bool = False

# Django Server Port
# This is the port where django server will be started on
DJANGO_BIND_PORT: int = 9999

# URLS to  be parsed right to django
# This is only useful for urls that were registered with django but not with duck .e.g /admin
# Regex urls are allowed
DJANGO_REGISTERED_URLS: list[str] = [
    "/admin",
]

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

# List of all middlewares as strings in form "middleware.MiddlewareClass"
# Make sure DuckToDjangoMetaDataShareMiddleware is in MIDDLEWARES so as to
# enable good cooperation between duck and django if Django is used as backend
# **Note**: CSRFMiddleware and SessionMiddleware will be removed if USE_DJANGO=True
# WARNING: The middlewares should be arranged in order at this point
MIDDLEWARES: list[str] = middlewares

#  Request Normalizers
# These Normalizers accept a Request object as an argument and return the Request object with normalized attributes.
NORMALIZERS: list[str] = normalizers

# STATIC FILES HANDLING

# The root directory for storing static files.
# Auto created if it does'nt exist
STATIC_ROOT: str = BASE_DIR / "staticfiles"

# The URL to use for serving static files.
STATIC_URL: str = "static/"

# MEDIA FILES HANDLING

# Media Root
# This is where the media files will reside in.
# Auto created if it does'nt exist
MEDIA_ROOT: str = BASE_DIR / "media"

# Media Url
# This is the url for serving media files
MEDIA_URL: str = "media/"

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
