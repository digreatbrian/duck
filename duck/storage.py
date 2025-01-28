"""
Defines and provides the storage directory for Duck-related data and configuration files.
"""

from os import path


def get_duck_storage():
    """
    Returns the absolute path of the Duck storage directory.

    This directory is intended for storing data, configuration files, or other resources
    required by the Duck application. The path is resolved based on the current location
    of this file.

    Returns:
        str: The absolute path to the Duck storage directory.
    """
    return path.abspath(path.dirname(__file__))


duck_storage = get_duck_storage()
