import importlib
import sys


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
