"""
Module containing react_frontend template tag implementation.
"""
from typing import Dict
from urllib.parse import urljoin

from duck.utils.safemarkup import (
    MarkupSafeString,
    mark_safe, 
)
from duck.settings import SETTINGS
from duck.exceptions.all import SettingsError
from duck.utils.path import (
    joinpaths,
    sanitize_path_segment,
    build_absolute_uri,
)
from duck.utils.importer import x_import
from duck.urls import path
from duck.meta import Meta


def get_space_indentation(text: str) -> str:
    """
    Returns the indentation for the text. (mostly the first spaces before the text)
    """
    firstline = text.split('\n', 1)[0]
    indentation = ""
    if not firstline:
        return ""
    for i in range(len(firstline) - 1):
        cha = firstline[i]
        indentation += " "
        if cha.strip():
            # we have reached a valid character not a whitespace
            break
    return indentation


def striplines(text: str) -> str:
    """
    Strip whitespaces in text for every line.
    """
    lines = text.splitlines()
    lines = [line.strip() for line in lines]
    return "\n".join(lines)


@mark_safe
def react_frontend(context: Dict, jsx_code: str) -> MarkupSafeString:
    """
    Saves and exposes the jsx code to a url endpoint.

    Args:
        jsx_code (str): The JSX code to be saved.
        
    Notes:
        - Nomatter how many this tag is used in a single template, the React scripts in settings.py 
        will be embedded once in the template to avoid code redundancy.
        
    Returns:
        str: The HTML code to load the React scripts (e.g babel source script) accompanied by html to retrieve the saved JSX code.
    """
    from duck.settings.loaded import FRONTEND
    
    scripts_blueprint = "duck.etc.apps.react_frontend.blueprint.ReactFrontend"
    if not FRONTEND:
        raise SettingsError("React fronted configuration not set in settings.py")
    
    if scripts_blueprint not in SETTINGS["BLUEPRINTS"]:
        raise SettingsError(
            f"Duck cannot serve React scripts because the required blueprint '{scripts_blueprint}' is missing. "
            f"Please ensure the '{scripts_blueprint}' blueprint is registered in your application."
        )
    
    # retrieve a unique ID for the jsx code
    try:
        server_url = Meta.get_absolute_server_url()
    except Exception:
        server_url = None
    
    jsx_code = striplines(jsx_code)
    jsx_code_store = x_import("duck.etc.apps.react_frontend.jsx_code_store.JsxCodeStore")
    cipher_script = x_import("duck.etc.apps.react_frontend.safescript.cipher_script")
    root_url = FRONTEND["REACT"]["root_url"]
    
    if server_url:
        root_url = build_absolute_uri(server_url, root_url)
    
    jsx_code_id = jsx_code_store.get_jsx_code_id(jsx_code)
    jsx_code_url = urljoin(sanitize_path_segment(root_url).rstrip("/"), f"?id={jsx_code_id}")
    
    jsx_code_store.update(jsx_code_id, jsx_code.strip()) # Add jsx code to store.
    request = context["request"]
    html = []
    
    if not request.META.get("REACT_SCRIPTS_NO_UPDATE"):
        # React scripts need to be embedded in template, they haven't been embedded yet.
        scripts_url = FRONTEND["REACT"]["scripts_url"]
        scripts_url = joinpaths(root_url, scripts_url)  # Final URL endpoint for serving React scripts defined in settings.py.
        for script in FRONTEND["REACT"]['scripts']:
            # Function `cipher_script` works as follows:
            # If script is a local filesystem path, the script will be ciphered and only remote scripts
            # in form 'https://some.site.com/script.js' will remain unciphered.
            script = cipher_script(script) # cipher script to ensure local filesystem is not exposed.
            script_url = urljoin(sanitize_path_segment(scripts_url), f"?href={script}")
            html.append( f'<script type="text/javascript" href="{script_url}"></script>')
        request.META["REACT_SCRIPTS_NO_UPDATE"] = True
    html.append(f'<script type="text/babel" href="{jsx_code_url}"></script>')
    return f"\n{get_space_indentation(jsx_code)}".join(html)
