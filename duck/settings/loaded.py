"""
Module for loading objects defined in `settings.py` or in the Duck application configuration.
Provides functions to retrieve various components and configurations dynamically.
"""

from typing import (Any, List, Dict, Tuple, Type, Coroutine)

from duck.etc.templatetags import (
    BUILTIN_TEMPLATETAGS,
)
from duck.template.templatetags import (
    TemplateTag,
    TemplateFilter,
    TemplateTagError,
)
from duck.exceptions.all import (
    MiddlewareLoadError,
    NormalizerLoadError,
    SettingsError, 
)
from duck.routes import Blueprint
from duck.settings import SETTINGS
from duck.automation import Automation
from duck.automation.dispatcher import AutomationDispatcher
from duck.automation.trigger import AutomationTrigger
from duck.http.core.proxyhandler import HttpProxyHandler
from duck.http.request import HttpRequest
from duck.html.components.templatetags import HtmlComponentTemplateTag
from duck.utils.importer import import_module_once, x_import


def get_wsgi() -> Any:
    """
    Returns the loaded WSGI application defined in `settings.py`.

    Raises:
        SettingsError: If `WSGI` is not defined or cannot be imported.
    """

    wsgi_path = SETTINGS.get("WSGI")
    if not wsgi_path:
        raise SettingsError("Please define WSGI in `settings.py`.")
    try:
        return x_import(wsgi_path)(SETTINGS)
    except Exception as e:
        raise SettingsError(f"Failed to load WSGI: {e}") from e


def get_file_upload_handler() -> Any:
    """
    Returns the file upload handler defined in `settings.py`.

    Raises:
        SettingsError: If `FILE_UPLOAD_HANDLER` is not defined or cannot be imported.
    """
    handler_path = SETTINGS.get("FILE_UPLOAD_HANDLER")
    if not handler_path:
        raise SettingsError(
            "Please define FILE_UPLOAD_HANDLER in `settings.py`.")
    try:
        return x_import(handler_path)
    except Exception as e:
        raise SettingsError(f"Failed to load file upload handler: {e}") from e


def get_user_templatetags() -> List[TemplateTag | TemplateFilter]:
    """
    Returns a list of template tags and filters defined in the settings.py.
    """
    module_str = SETTINGS["TEMPLATETAGS_MODULE"]
    if not module_str:
        return []
    try:
        templatetags = import_module_once(module_str).TEMPLATE_TAGS
        templatetags = templatetags or []
        return list(templatetags)
    except Exception as e:
        raise SettingsError(f"Failed to templatetags: {str(e)}")


def get_html_component_tags() -> List[HtmlComponentTemplateTag]:
    """
    Returns loaded HTML component template tags defined in `settings.py`.

    Raises:
        SettingsError: If any component cannot be imported or instantiated.
    """
    component_tags = []
    try:
        for name, cls_path in SETTINGS.get("HTML_COMPONENTS", {}).items():
            cls = x_import(cls_path)
            try:
                component_tags.append(HtmlComponentTemplateTag(name, cls))
            except (TemplateTagError):
                # template tag already in existence
                component_tags.append(HtmlComponentTemplateTag.get_tag(name))
    except Exception as e:
        raise SettingsError(f"Error loading HTML components: {e}") from e
    return component_tags


def get_request_class() -> Type[Any]:
    """
    Returns the request class defined in `settings.py`.

    Raises:
        SettingsError: If `REQUEST_CLASS` is not defined or cannot be imported.
    """
    request_class = SETTINGS.get("REQUEST_CLASS")
    if not request_class:
        raise SettingsError("Please define REQUEST_CLASS in `settings.py`.")
    try:
        request_class = x_import(request_class)
        if not issubclass(request_class, HttpRequest):
            raise Exception(
                "Invalid request class, should be a subclass of HttpRequest.")
        return request_class
    except Exception as e:
        raise SettingsError(f"Failed to load request class: {e}") from e


def get_content_compression_settings():
    """
    Returns the content compression settings defined in `settings.py`.

    Raises:
        SettingsError: If `CONTENT_COMPRESSION` is not defined or cannot be imported.
    """
    content_compression = SETTINGS.get("CONTENT_COMPRESSION")
    if not content_compression:
        raise SettingsError(
            "Please define CONTENT_COMPRESSION in `settings.py`.")
    try:
        if not isinstance(content_compression, dict):
            raise SettingsError("CONTENT_COMPRESSION should be a dictionary.")
        encoding = content_compression.get("encoding")
        if encoding not in ("gzip", "deflate", "br", "identity"):
            raise SettingsError(
                f"Invalid encoding: {encoding}. Must be one of 'gzip', 'deflate', 'identity' or 'br'."
            )
        if encoding == "br":
            try:
                pass
            except ImportError as e:
                raise SettingsError(
                    "Brotli decompression requires brotli library, please install it first using `pip install brotli`"
                ) from e
        return content_compression
    except Exception as e:
        raise SettingsError(
            f"Failed to load content compression settings: {e}") from e


def get_proxy_handler() -> Type[Any]:
    """
    Returns loaded proxy handler class.
    """
    proxy_handler = SETTINGS.get("PROXY_HANDLER")
    if not proxy_handler:
        raise SettingsError("Please define PROXY_HANDLER in `settings.py`.")
    try:
        proxy_handler = x_import(proxy_handler)
        if not issubclass(proxy_handler, HttpProxyHandler):
            raise Exception(
                "Invalid proxy handler, should be a subclass of HttpProxyHandler."
            )
        return proxy_handler
    except Exception as e:
        raise SettingsError(f"Failed to load proxy handler: {e}") from e


def get_automation_dispatcher() -> AutomationDispatcher:
    """
    Returns the automation dispatcher defined in `settings.py`.

    Raises:
        SettingsError: If `AUTOMATION_DISPATCHER` is not properly defined.
    """
    dispatcher_path = SETTINGS.get("AUTOMATION_DISPATCHER")
    if not dispatcher_path:
        raise SettingsError(
            "AUTOMATION_DISPATCHER is not set in `settings.py`. Ensure `RUN_AUTOMATIONS=True`."
        )
    try:
        dispatcher = x_import(dispatcher_path)
        if not issubclass(dispatcher, AutomationDispatcher):
            raise SettingsError(
                f"AUTOMATION_DISPATCHER should be a subclass of AutomationDispatcher, not {dispatcher}."
            )
        return dispatcher
    except Exception as e:
        raise SettingsError(
            f"Failed to load automation dispatcher: {e}") from e


def get_triggers_and_automations(
) -> List[Tuple[AutomationTrigger, Automation]]:
    """
    Returns all triggers and their corresponding automations defined in `settings.py`.

    Raises:
        SettingsError: If any trigger or automation is invalid or improperly configured.
    """
    automations = []
    try:
        for idx, (automation_path,
                  meta) in enumerate(SETTINGS.get("AUTOMATIONS", {}).items()):
            try:
                automation = x_import(automation_path)
            except ImportError:
                raise SettingsError(
                    f"Cannot import automation '{automation_path}' ")

            if not isinstance(automation, Automation):
                raise SettingsError(
                    f"Automation '{automation_path}' at position {idx} must be an instance of Automation, not {type(automation).__name__}."
                )
            if not isinstance(meta, dict):
                raise SettingsError(
                    f"AUTOMATIONS in settings should map Automations to dictionaries, not {type(meta).__name__}."
                )
            trigger_path = meta.get("trigger")
            if not trigger_path:
                raise SettingsError(
                    f"Automation '{automation_path}' at position {idx} must have a corresponding dictionary with key 'trigger' set."
                )
            try:
                trigger = x_import(trigger_path)
            except ImportError:
                raise SettingsError(
                    f"Cannot import automation trigger '{trigger_path}' ")
            if not isinstance(trigger, AutomationTrigger):
                raise SettingsError(
                    f"Trigger for automation '{automation_path}' at position {idx} must be an instance of AutomationTrigger, not {type(trigger).__name__}."
                )
            try:
                trigger.check_trigger()  # check if this method is implemented
            except NotImplementedError:
                raise SettingsError("Method 'check_trigger' not implemented")
            automations.append((trigger, automation))
    except Exception as e:
        raise SettingsError(f"Error loading automations: {e}")
    return automations


def get_blueprints() -> List[Blueprint]:
    """
    Returns necessary loaded blueprints.

    Notes:
        - In condition that the user hasn't defined urlpatterns and blueprints,
         or all of the defined blueprints are builtins,
        Duck's default site blueprint will be added blueprints list.
    """
    ducksite_blueprint = x_import("duck.etc.apps.defaultsite.blueprint.DuckSite")
    blueprints = SETTINGS["BLUEPRINTS"]
    final_blueprints = []
    builtins_count = 0  # number of builtin blueprints

    try:
        for i in blueprints:
            blueprint = x_import(i)
            if not isinstance(blueprint, Blueprint):
                raise SettingsError(
                    f'Blueprint "{i}" should be an instance of Blueprint not {type(blueprint)}'
                )
            if blueprint.is_builtin:
                builtins_count += 1
            final_blueprints.append(blueprint)
        if not URLPATTERNS and len(blueprints) == builtins_count:
            # no urlpatterns defined
            # no blueprints defined or all of the defined blueprints are builtins
            final_blueprints.append(ducksite_blueprint)
        return final_blueprints
    except Exception as e:
        raise SettingsError(f"Error loading blueprints: {e}") from e


def get_user_urlpatterns():
    """
    Returns urlpatterns defined in URLPATTERNS_MODULE in settings.py
    """
    try:
        urlpatterns_mod = import_module_once(SETTINGS["URLPATTERNS_MODULE"])
        return urlpatterns_mod.urlpatterns
    except Exception as e:
        raise SettingsError(f"Error loading urlpatterns: {e}") from e


def get_user_middlewares():
    """
    Returns loaded middlewares set in settings.py
    """
    try:
        middlewares = [x_import(m) for m in SETTINGS["MIDDLEWARES"]]
        return middlewares
    except Exception as e:
        raise MiddlewareLoadError("Error loading middlewares: %s" % str(e)) from e


def get_normalizers():
    """
    Returns loaded normalizers set in settings.py
    """
    try:
        normalizers = [
            x_import(normalizer) for normalizer in SETTINGS["NORMALIZERS"]
        ]
        return normalizers
    except Exception as e:
        raise NormalizerLoadError("Error loading normalizers: %s" % str(e)) from e


def get_session_storage():
    """
    Returns the session storage class defined in settings.py.
    """
    return x_import(SETTINGS["SESSION_STORAGE"])  # import session storage


def get_session_store():
    """
    Returns the session store class.
    """
    session_engine = SETTINGS["SESSION_ENGINE"]
    return import_module_once(session_engine).SessionStore  # get SessionStore from session engine.


def get_frontend() -> Dict[str, Dict[str, str]]:
    """
    Returns the frontend settings for Duck.
    """
    frontend = SETTINGS["FRONTEND"]
    frontend = frontend or {}
    react_settings = {}
    
    if not frontend:
        return frontend
    
    try:
        for key, value in frontend.items():
            if key != "REACT":
                raise SettingsError("Fronted configuration invalid, only React fronted supported.")
            else:
                react_settings = frontend["REACT"]
        if "scripts" not in react_settings.keys():
             raise SettingsError("Frontend configuration for React should contain `scripts`.")
        else:
             scripts = react_settings.get("scripts")
             if not scripts:
                 raise SettingsError("Scripts for React fronted configuration not set.")
        if "root_url" not in react_settings.keys():
             raise SettingsError("Frontend configuration for React should contain `root_url`.")
        else:
             root_url = react_settings.get("root_url")
             if not root_url:
                 raise SettingsError("Root URL for React frontend configuration not set.")
        if "scripts_url" not in react_settings.keys():
             raise SettingsError("Frontend configuration for React should contain `scripts_url`.")
        else:
             scripts_url = react_settings.get("scripts_url")
             if not scripts_url:
                 raise SettingsError("Scripts URL for React frontend configuration not set.")
    except Exception as e:
       raise SettingsError(f"Error loading frontend: {str(e)}")
    return frontend


def get_request_handling_task_executor():
    """
    Returns the request handling callable for executing 
    request handling threads and coroutines.
    """
    try:
        request_handling_task_executor = x_import(SETTINGS["REQUEST_HANDLING_TASK_EXECUTOR"])
        kwargs = SETTINGS["REQUEST_HANDLING_TASK_EXECUTOR_KWARGS"] or {}
        return request_handling_task_executor(**kwargs)
    except Exception as e:
        raise SettingsError(f"Error loading request handling task executor: {e}") from e


# Initialize components based on settings
WSGI = get_wsgi()

FILE_UPLOAD_HANDLER = get_file_upload_handler()

USER_TEMPLATETAGS = get_user_templatetags()

HTML_COMPONENT_TAGS = (
    get_html_component_tags()
    if  SETTINGS.get("ENABLE_HTML_COMPONENTS")
    else []
)

ALL_TEMPLATETAGS = HTML_COMPONENT_TAGS  + USER_TEMPLATETAGS + BUILTIN_TEMPLATETAGS

REQUEST_CLASS = get_request_class()

CONTENT_COMPRESSION = get_content_compression_settings()

PROXY_HANDLER = get_proxy_handler() if SETTINGS["USE_DJANGO"] else None

AUTOMATION_DISPATCHER, AUTOMATIONS = (
    get_automation_dispatcher(), get_triggers_and_automations()
    if SETTINGS.get("RUN_AUTOMATIONS")
    else (None, []), 
)

URLPATTERNS = get_user_urlpatterns()

BLUEPRINTS = get_blueprints()

MIDDLEWARES = get_user_middlewares()

NORMALIZERS = get_normalizers()

SESSION_STORAGE = get_session_storage()

SESSION_STORE = get_session_store()

FRONTEND = get_frontend()

REQUEST_HANDLING_TASK_EXECUTOR = get_request_handling_task_executor()
