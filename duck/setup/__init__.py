"""
Module for setting up Duck space and configure all necessary components to ensure the application is ready for operation.
"""

import os
import sys
import asyncio
from typing import List

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
    REQUEST_HANDLING_TASK_EXECUTOR,
)
from duck.backend.django.setup import prepare_django
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


def register_urlpatterns(urlpatterns: List):
    """
    Register some application urlpatterns.
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
    Register application blueprints.
    """
    # Register route blueprint.urlpatterns
    for blueprint in blueprints:
        try:
            register_urlpatterns(blueprint.urlpatterns)
        except Exception as e:
            raise BlueprintError(f"Error registering urlpatterns for blueprint '{blueprint}' ") from e


def set_asyncio_loop():
    """
    Configure the event loop policy based on SETTINGS["ASYNC_LOOP"].

    Supports:
    - "asyncio": Default Python event loop (no changes made)
    - "uvloop": High-performance event loop (requires uvloop installed)

    Raises:
        SettingsError: If the specified ASYNC_LOOP value is unsupported.
    """
    supported_loops = {"asyncio", "uvloop"}
    loop_choice = SETTINGS.get("ASYNC_LOOP", "asyncio")

    # Only configure the loop if async handling is enabled or HTTP/2 is used
    if SETTINGS.get("ASYNC_HANDLING") or SETTINGS.get("SUPPORT_HTTP_2"):
        if loop_choice not in supported_loops:
            raise SettingsError(
                f"Invalid ASYNC_LOOP setting: '{loop_choice}'. "
                f"Supported options are: {sorted(supported_loops)}."
            )

        if loop_choice == "uvloop":
            try:
                import uvloop
            except ImportError as e:
                raise SettingsError("uvloop is not installed, but ASYNC_LOOP is set to 'uvloop'.") from e
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def setup(make_app_dirs: bool = True):
    """
    Setup the Duck application.

    Initialize and configure all necessary components to ensure the application is ready for operation.

    Args:
            make_app_dirs (bool): Whether to create application directories which might be useful to the project.
    Notes:
        - This configures and registers all routes either simple or ones created
    """
    base_dir = str(SETTINGS['BASE_DIR'])
    
    # Set asyncio event loop for ASYNC_HANDLING or HTTP/2
    set_asyncio_loop()
    
    # Create base application directories
    if make_app_dirs:
        makedirs()  # app dirs creation

    if SETTINGS["USE_DJANGO"]:
        PortRecorder.add_new_occupied_port(
            SETTINGS["DJANGO_BIND_PORT"],
            "DJANGO_BIND_PORT",
        )
        
    register_urlpatterns(URLPATTERNS)
    register_blueprints(BLUEPRINTS)
    
    if base_dir not in sys.path:
        # Add project directory to path
        sys.path.insert(-1, base_dir)
    
    try:
        prepare_django(True)
    except Exception:
        pass
    
    # Initialize the RequestHandlingExecutor lazily after prepare_django as this line will
    # make the whole setup very slow.
    REQUEST_HANDLING_TASK_EXECUTOR() # load executor lazilyu
