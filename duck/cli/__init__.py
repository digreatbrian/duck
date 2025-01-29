import os


def add_to_pythonpath(path: str):
    """
    Retrieves the current PYTHONPATH environment variable and returns it.

    Args:
        path (str): The directory to check in the current PYTHONPATH.

    Returns:
        str: The current PYTHONPATH value.
    """
    current_pythonpath = os.environ.get('PYTHONPATH', '')
    
    if not current_pythonpath:
        return path
    return current_pythonpath + os.pathsep + path
