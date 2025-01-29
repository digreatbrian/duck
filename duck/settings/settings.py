"""
Provides access to application settings
"""
import os
import sys
import importlib

from duck.exceptions.all import SettingsError
from duck.utils.importer import import_module_once

os.environ.setdefault("DUCK_SETTINGS_MODULE", "settings")

SETTINGS_MODULE = os.environ.get("DUCK_SETTINGS_MODULE")


def settings_to_dict(settings_module: str) -> dict:
    """Converts a settings module to a dictionary.

    Args:
            settings_module (str): The path to the settings module.

    Returns:
            dict: A dictionary containing the settings from the module.

    Raises:
            ImportError: If the settings module cannot be imported.
    """
    settings_mod = import_module_once(settings_module)
    settings = {}
    for var in dir(settings_mod):
        if var.isupper():
            # is a valid setting variable
            settings[var] = getattr(settings_mod, var)
    return settings


def get_combined_settings() -> dict:
    """Combines default and user settings into a single dictionary.

    Reads the default settings from `duck.etc.settings` and attempts to
    read user settings from a `settings` module in the current directory.

    Returns:
            dict: A dictionary containing the combined settings.

    Raises:
            SettingsError: If there's an error loading user settings.
    """
    default_settings = settings_to_dict("duck.etc.settings")
    try:
        user_settings = settings_to_dict(SETTINGS_MODULE)
    except Exception as e:
        raise SettingsError(
            f"Error loading Duck settings module, ensure environment variable DUCK_SETTINGS_MODULE is set correctly: {e}."
        ) from e

    settings = {**default_settings, **user_settings}
    
    return settings


# Set and load important settings, objects, etc.
SETTINGS = get_combined_settings()
