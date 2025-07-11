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
        from duck.backend.django.bridge import find_manage_py
        
        python_path = SETTINGS["PYTHON_PATH"]
        manage_py = find_manage_py()
        base_dir = str(SETTINGS['BASE_DIR'])
        command_args = []
        
        keyword_reached = False
        for arg in sys.argv:
            if not keyword_reached:
                if arg.strip() == "django":
                    keyword_reached = True
            else:
                command_args.append(arg)
        
        command = [python_path, manage_py]
        command.extend(command_args)   
        subprocess.call(command, cwd=base_dir, env={**os.environ, "PYTHONPATH": add_to_pythonpath(base_dir)})
