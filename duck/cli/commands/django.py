"""
Module containing django command class.
"""
import os
import sys
import subprocess

from duck.logging import console
from duck.utils.importer import x_import
from duck.utils.path import joinpaths
from duck.cli import add_to_pythonpath


class DjangoCommand:
    # django command
    
    @classmethod
    def setup(cls):
        # Setup before command execution
        pass
    
    @classmethod
    def main(cls):
        cls.setup()
        cls.django()
        
    @classmethod
    def django(cls):
        # Execute command after setup.
        # This command uses sys.argv to retrieve command arguments.
        
        from duck.settings import SETTINGS
        from duck.backend.django.bridge import DUCK_APP_MODULE
        
        python_path = SETTINGS["PYTHON_PATH"]
        django_app_home = DUCK_APP_MODULE.__path__[0]
        command_args = []
        
        keyword_reached = False
        for arg in sys.argv:
            if not keyword_reached:
                if arg.strip() == "django":
                    keyword_reached = True
            else:
                command_args.append(arg)
        
        command = [python_path, joinpaths(django_app_home, "manage.py")]
        command.extend(command_args)
        
        root_dir = os.path.abspath('.')
        subprocess.call(command, cwd=root_dir, env={**os.environ, "PYTHONPATH": add_to_pythonpath(root_dir)})
