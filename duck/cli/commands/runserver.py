"""
Module containing runserver command class.
"""
import os
import subprocess

from typing import Optional
from duck.logging import console


class RunserverCommand:
    # runserver command
    
    @classmethod
    def setup(cls, settings_module: Optional[str] = None):
        # Setup before command execution
        if settings_module:
            os.environ["DUCK_SETTINGS_MODULE"] = settings_module
    
    @classmethod
    def main(
        cls,
        address: str = "0.0.0.0",
        port: int = 8000,
        domain: Optional[str] = None,
        settings_module: Optional[str] = None,
        mainfile: Optional[str] = None,
        uses_ipv6: bool = False,
        reload: bool = False,
    ):
        cls.setup(settings_module)
        
        # Runserver
        cls.runserver(
            address=address,
            port=port,
            domain=domain,
            mainfile=mainfile,
            uses_ipv6=uses_ipv6,
            reload=reload)
    
    @classmethod
    def runserver(
         cls,
         address: str = "0.0.0.0",
         port: int = 8000,
         domain: Optional[str] = None,
         mainfile: Optional[str] = None,
         uses_ipv6: bool = False,
         reload: bool = False,
     ):
        
        from duck.app import App
        from duck.settings import SETTINGS
        
        if mainfile:
            # file containing app instance provided
            if not mainfile.endswith(".py"):
                raise TypeError(
                    "File provided as the main python file has invalid extension, should be a .py file."
                )
    
            if not os.path.isfile(mainfile):
                raise FileNotFoundError(
                    "Main python file which the app resides not found.")
    
            # Log something
            console.log_raw("All flags and arguments are ignored!", level=console.WARNING)
            
            # Execute sub-command
            command = [SETTINGS["PYTHON_PATH"], mainfile]
            
            if reload:
                command.extend(["--reload"])
            
            # Execute the command in a subprocess
            subprocess.call(command, start_new_session=False)  # run command as child process
        
        else:
            application = App(
                addr=address,
                port=port,
                domain=domain,
                uses_ipv6=uses_ipv6)
           
             # If --reload arg in sys.argv, app will be restarted nomatter if run was called instead.
            application.run()  
