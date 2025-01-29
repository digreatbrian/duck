"""
Module containing runtests command class.
"""
import os
import subprocess

from duck.logging import console
from duck.storage import duck_storage
from duck.utils.path import joinpaths


class RuntestsCommand:
    # runtests command
    
    @classmethod
    def setup(cls):
        # Setup before command execution
        # Setup minimum settings module for CLI to function correctly
        os.environ.setdefault("DUCK_SETTINGS_MODULE", "duck.etc.structures.projects.testing.settings")
        
    @classmethod
    def main(cls):
        cls.setup()
        cls.runtests()
     
    @classmethod
    def runtests(cls):
        # Execute command after setup.
        from duck.settings import SETTINGS
        
        python_path = SETTINGS["PYTHON_PATH"]
        tests_dir = joinpaths(duck_storage, "tests")
        
        subprocess.call([
            python_path, "-m", "unittest", "discover", "-s",
            tests_dir, "-p", "test_*.py", "-t", tests_dir
        ])
