"""
Module containing function for including bulk HTML components in a module.
"""
import inspect
from typing import List, Dict

from duck.html.components import HtmlComponent
from duck.utils.string import is_pascal_case
from duck.utils.importer import import_module_once


BASE_MODULE = "duck.html.components"

BUILTIN_COMPONENTS = [
    f"{BASE_MODULE}.{module}" for module in [
        "card",
        "icon",
        "link",
        "form",
        "script",
        "style",
        "input",
        "textarea",
        "select",
        "image",
        "video",
        "hero",
        "container",
        "checkbox",
        "navbar",
        "footer",
        "button",
        "popup",
        "code",
        "label",
        "fileinput",
        "table_of_contents",
    ]
]


def components_include(modules: List[str]) -> Dict[str, str]:
    """
    This looks up HTML components in the provided modules and returns a dictionary.

    Args:
        modules (List[str]): The list of module names containing HTML components in PascalCase.

    Returns:
        Dict[str, str]: A dictionary mapping component names to their full module path.
    """
    components = {}
    
    for mod_name in modules:
        mod = import_module_once(mod_name)  # Ensure module is imported
        
        if not mod:
            continue  # Skip if import fails

        for attr_name in dir(mod):
            if is_pascal_case(attr_name):  # Ensure it's PascalCase
                cls = getattr(mod, attr_name)
                if inspect.isclass(cls) and issubclass(cls, HtmlComponent):
                    components[attr_name] = f"{mod_name}.{attr_name}"  # Correct dictionary assignment

    return components
