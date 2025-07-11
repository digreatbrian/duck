"""
Defines and provides the storage directory for Duck-related data and configuration files.
"""

from os import path, getenv
from pathlib import Path
from functools import lru_cache

from duck.utils.importer import import_module_once
from duck.exceptions.all import SettingsError


def get_duck_storage() -> str:
    """
    Returns the absolute path of the Duck storage directory.

    This directory is intended for storing data, configuration files, or other resources
    required by the Duck application. The path is resolved based on the current location
    of this file.

    Returns:
        str: The absolute path to the Duck storage directory.
    """
    return path.abspath(path.dirname(__file__))


@lru_cache(maxsize=1)
def BaseDir() -> Path:
    """
    Returns the Base Directory for Duck project based on environment variable `DUCK_SETTINGS_MODULE`. 
    
    Notes:
    - This useful if you want to have the same base directory everywhere nomatter which settings you are using.
    """
    try:
        settings_path = getenv("DUCK_SETTINGS_MODULE")
        settings_mod = import_module_once(settings_path)
        return Path(settings_mod.__file__).resolve().parent
    except (ImportError, ModuleNotFoundError, KeyError) as e:
        raise SettingsError(
            f"Error loading Duck settings module, ensure environment variable DUCK_SETTINGS_MODULE is set correctly: {e}."
        ) from e

    
duck_storage = get_duck_storage()
