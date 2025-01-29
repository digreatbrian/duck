"""
Module containing functions to create and delete Duck temporary project structure.
"""

URLPATTERN_MODULE = """
urlpatterns = []
"""

def create_temp_project(_dir: str = "."):
    """
    Creates temporary project structure with minimum setup.
    """
    file = os.path.join(_dir, "settings.py")
    if not os.path.isfile(file):
        with open(file, "a"):
            pass


def remove_temp_project(_dir: str = "."):
    """
    Removes temporary empty settings.py file.
    """
    file = os.path.join(_dir, "settings.py")
    if os.path.isfile(file):
        with open(file, "r") as fd:
            if not fd.read():
                os.unlink(file)  # remove file if empty.
