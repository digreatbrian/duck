"""
Provides access to application settings.
"""
import os
import sys
import importlib

from duck.exceptions.all import SettingsError
from duck.utils.importer import import_module_once

os.environ.setdefault("DUCK_SETTINGS_MODULE", "settings")

SETTINGS_MODULE = os.environ.get("DUCK_SETTINGS_MODULE")


class Settings(dict):
    """
    A class for managing Duck settings.
    
    This class extends the built-in `dict` to store settings in a dictionary-like format.
    It also provides a custom representation of the settings for debugging and logging.
    """
    source = None
    
    def __repr__(self):
        # Provide a more detailed and readable string representation of the Settings object
        return (
           "<" + f"{self.__class__.__name__} "
            f"source={repr(self.source)}".replace('<', "[").replace('>', "]") + ">"
        )


def settings_to_dict(settings_module: str) -> Settings:
    """Converts a settings module to a dictionary.

    Args:
            settings_module (str): The path to the settings module.

    Returns:
            Settings: Settings object derived from a dictionary containing the settings.

    Raises:
            ImportError: If the settings module cannot be imported.
    """
    settings_mod = import_module_once(settings_module)
    settings = Settings({})
    settings.source = settings_mod
    
    for var in dir(settings_mod):
        if var.isupper():
            # is a valid setting variable
            settings[var] = getattr(settings_mod, var)
    
    return settings


def get_combined_settings() -> Settings:
    """Combines default and user settings into a single dictionary.

    Reads the default settings from `duck.etc.settings` and attempts to
    read user settings from a `settings` module in the current directory.

    Returns:
            Settings: Settings object derived from a dictionary containing the settings.

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
    
    # Update the default settings with custom ones.
    default_settings.update(user_settings)
    settings = Settings(default_settings)
    settings.source = user_settings.source
    return settings


# Set and load important settings, objects, etc.
SETTINGS: Settings = get_combined_settings()

if os.getenv("DUCK_USE_DJANGO", None) == "true":
    SETTINGS["USE_DJANGO"] = True
