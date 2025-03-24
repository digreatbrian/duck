"""
Module, object and variable importation module.
"""
import importlib
import importlib.util
import sys
import os


def import_module_once(module_name):
    """Import a module only once"""
    if module_name not in sys.modules:
        module = importlib.import_module(module_name)
        sys.modules[module_name] = module
    return sys.modules[module_name]


def x_import(object_path):
    """
    Function to import an object or class from a path e.g. `os.path.Path`
    """
    if object_path.count(".") < 1:
        return importlib.import_module(object_path)
    module_path, obj_name = object_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, obj_name)


def import_from_path(module_name, file_path):
    """
    Dynamically imports a module from a specified file path.

    This function loads a Python module from a given file path without modifying
    `sys.path`, making it useful for importing external or dynamically generated modules.

    Args:
        module_name (str): The name to assign to the imported module.
        file_path (str): The absolute or relative path to the module file.

    Returns:
        module: The imported module object.

    Raises:
        ImportError: If the module cannot be loaded from the given path.
    """
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    
    if spec is None:
        raise ImportError(f"Cannot load module {module_name} from {file_path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
