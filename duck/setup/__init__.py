"""
Module for setting up Duck space and configure all necessary components to ensure the application is ready for operation.
"""

import os

from duck.exceptions.all import (
    SettingsError,
    BlueprintError,
    RouteError,
)
from duck.routes import RouteRegistry
from duck.settings import SETTINGS
from duck.settings.loaded import (
    BLUEPRINTS,
    URLPATTERNS,
)
from duck.utils.port_recorder import PortRecorder


def makedirs():
    """
    Initial function for Duck application directories creation.
    """
    # TEMPLATE_DIRS setup
    tdirs = str(SETTINGS["TEMPLATE_DIRS"])
    
    if isinstance(tdirs, (list)):
        for tdir in tdirs:
            os.makedirs(tdir, exist_ok=True)

    # STATIC_ROOT setup
    sroot = SETTINGS["STATIC_ROOT"]
    if os.path.isfile(sroot):
        raise SettingsError(
            "STATIC_ROOT in settings.py should be a directory not a file")

    if sroot and not os.path.isdir(sroot):
        os.makedirs(sroot, exist_ok=True)

    # SESSION_DIR setup
    sdir = SETTINGS["SESSION_DIR"]
    if os.path.isfile(sdir):
        raise SettingsError(
            "SESSION_DIR in settings.py should be a directory not a file")

    if sdir and not os.path.isdir(sdir):
        os.makedirs(sdir, exist_ok=True)

    # STATIC_ROOT setup
    sroot = SETTINGS["STATIC_ROOT"]
    if os.path.isfile(sroot):
        raise SettingsError(
            "STATIC_ROOT in settings.py should be a directory not a file")

    if sroot and not os.path.isdir(sroot):
        os.makedirs(sroot, exist_ok=True)

    # MEDIA_ROOT setup
    mroot = SETTINGS["MEDIA_ROOT"]
    if os.path.isfile(mroot):
        raise SettingsError(
            "MEDIA_ROOT in settings.py should be a directory not a file")

    if mroot and not os.path.isdir(mroot):
        os.makedirs(mroot, exist_ok=True)

    # FILE_UPLOAD_DIR setup
    fdir = SETTINGS["FILE_UPLOAD_DIR"]
    if os.path.isfile(fdir):
        raise SettingsError(
            "FILE_UPLOAD_DIR in settings.py should be a directory not a file")

    if fdir and not os.path.isdir(fdir):
        os.makedirs(fdir, exist_ok=True)

    # LOGGING_DIR setup
    ldir = SETTINGS["LOGGING_DIR"]
    if os.path.isfile(ldir):
        raise SettingsError(
            "LOGGING_DIR in settings.py should be a directory not a file")

    if ldir and not os.path.isdir(ldir):
        os.makedirs(ldir, exist_ok=True)


def register_urlpatterns(urlpatterns: list):
    """
    Register urlpatterns.
    """
    # register route urlpatterns
    for urlpattern in urlpatterns:
        try:
            if urlpattern.regex:
                # this is a regex urlpattern
                url, handler, name, methods = (
                        urlpattern['url'], 
                        urlpattern['handler'],
                        urlpattern['name'],
                        urlpattern['methods']
                  )
                RouteRegistry.regex_register(
                       url, handler, name, methods,
                )
            else:
                # this is a normal urlpattern
                url, handler, name, methods = (
                        urlpattern['url'], 
                        urlpattern['handler'],
                        urlpattern['name'],
                        urlpattern['methods']
                )
                RouteRegistry.register(
                        url, handler, name, methods,
                )
        except Exception as e:
            raise RouteError(f"Error registering URL pattern '{urlpattern}': {e}")


def register_blueprints(blueprints: list):
    """
    Register blueprints.
    """
    # register route blueprint.urlpatterns
    for blueprint in blueprints:
        try:
            register_urlpatterns(blueprint.urlpatterns)
        except Exception as e:
            raise BlueprintError(f"Error registering urlpatterns for blueprint '{blueprint}' ") from e


def setup(make_app_dirs: bool = True):
    """
    Setup the Duck application.

    Initialize and configure all necessary components to ensure the application is ready for operation.

    Args:
            make_app_dirs (bool): Whether to create application directories which might be useful to the project.
    Notes:
        - This configures and registers all routes either simple or ones created
    """
    if make_app_dirs:
        makedirs()  # app dirs creation

    if SETTINGS["USE_DJANGO"]:
        PortRecorder.add_new_occupied_port(
            SETTINGS["DJANGO_BIND_PORT"],
            "DJANGO_BIND_PORT",
        )
    register_urlpatterns(URLPATTERNS)
    register_blueprints(BLUEPRINTS)
