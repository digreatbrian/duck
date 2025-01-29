"""
Module containing collectscripts command class.
"""
import os
import requests
import pathlib
from typing import List

from duck.logging import console
from duck.utils.path import joinpaths, is_absolute_url
from duck.utils.urlcrack import URL


class CollectScriptsCommand:
    # collectscripts command
    @classmethod
    @property
    def static_root(cls) -> str:
        """
        Returns the static root directory.
        """
        from duck.settings import SETTINGS
        return str(SETTINGS["STATIC_ROOT"])
    
    @classmethod
    @property
    def destination_dir(cls,) -> str:
        """
        Returns the destination directory for scripts.
        """
        return joinpaths(cls.static_root, "react_frontend/scripts")
    
    @classmethod
    def to_destination_local_path(cls, script: str):
        """
        Returns the destination local path for the provided script.
        
        Args:
            script (str): Local path or remote url for the script e.g ./scripts/script.js or https://some.site/script.js
        """
        parse_result = URL(script)
        
        if not parse_result.scheme:
             # script is a local path.
             destination_script_path = joinpaths(cls.destination_dir, script.lstrip("."))
        else:
             # script is a remote url.
             destination_script_path = joinpaths(cls.destination_dir, script.split("://", 1)[-1])
        return destination_script_path
        
    @classmethod
    def setup(cls,):
        # Setup everything
        pass
    
    @classmethod
    def main(cls, skip_confirmation: bool = False):
        cls.setup()
        cls.collectscripts(skip_confirmation)
   
    @classmethod
    def collectscripts(cls, skip_confirmation: bool = False) -> None:
        """
        Collects scripts in FRONTEND and save them locally.
        """
        from duck.settings.loaded import FRONTEND
        
        if not FRONTEND:
            console.log_raw(
                "Frontend configuration for React not set, ensure the variable FRONTEND is set correctly in settings.py and try again.",
                level=console.WARNING)
            return
        
        scripts = FRONTEND["REACT"]["scripts"]
        missing_remote_scripts = []  # local scripts missing in local destination directory.
        missing_local_scripts = []  # local scripts missing in local destination directory.
        
        for script in scripts:
            destination_script_path = cls.to_destination_local_path(script)
            if not os.path.isfile(destination_script_path):
                # script not available locally.
                if is_absolute_url(script):
                    missing_remote_scripts.append(script)
                else:
                    missing_local_scripts.append(script)
        
        if missing_local_scripts or missing_remote_scripts:
            if missing_local_scripts:
                # Some local scripts are missing
                if not skip_confirmation:
                    console.log_raw(
                        f"Would you like to copy {len(missing_local_scripts)} missing script(s) (y/N): ",
                        level=console.DEBUG,
                        end="")
                    
                    # Obtain choice from prompt
                    choice = input("")
                    
                    if choice.lower().startswith('y'):
                        # Copy missing local scripts
                        cls.copy_missing_local_scripts(missing_local_scripts)
                    else:
                        console.log_raw("Skipped copy of local missing scripts!", custom_color=console.Fore.YELLOW)
                        console.log_raw(f"\nScripts: {missing_local_scripts}", custom_color=console.Fore.YELLOW)
                else:
                    # Copy local missing scripts
                    cls.copy_missing_local_scripts(missing_local_scripts)
            
            if missing_remote_scripts:
                # Some remote scripts are missing
                if not skip_confirmation:
                    console.log_raw(
                        f"\nWould you like to download {len(missing_remote_scripts)} missing script(s) (y/N): ",
                        level=console.DEBUG,
                        end="")
                    
                    # Obtain choice from prompt
                    choice = input("")
                    
                    if choice.lower().startswith('y'):
                        # Download and save missing local scripts
                        cls.download_missing_remote_scripts(missing_remote_scripts)
                    else:
                        console.log_raw("Skipped download of missing remote scripts!", custom_color=console.Fore.YELLOW)
                        console.log_raw(f"\nScripts: {missing_remote_scripts}", custom_color=console.Fore.YELLOW)
                else:
                    # Download and save missing local scripts
                    cls.download_missing_remote_scripts(missing_remote_scripts)
        else:
            if not scripts:
                # No scripts to collect, scripts are empty
                console.log_raw("Nothing to collect, scripts are empty!", level=console.WARNING)
            else:
                # All scripts are locally available.
                console.log_raw("Nothing to collect, script(s) seem to be locally available!", level=console.WARNING)
    
    @classmethod
    def copy_missing_local_scripts(cls, scripts: List[str]):
        """
        Copies local missing scripts to the destination scripts directory.
        """
        def save_script(script, content):
            """
            Saves the script with the provided content.
            """
            cls.save_script(script, content)
            console.log_raw(f"Script '{script}' successfully copied!", custom_color=console.Fore.GREEN)
        
        for script in scripts:
            if is_absolute_url(script):
                # Script unexpected, expected a local script but got a remote script instead.
                console.log_raw(f"Skipping, expected a local file but got a remote url: {script}")
                continue
            
            if not os.path.isfile(script):
                # Local script is not available
                raise FileNotFoundError(f"Script '{script}' is required but cannot be found")
            
            with open(script, "rb") as fd:
                # Save script to correct destination
                save_script(script, fd.read())
            
    @classmethod
    def save_script(cls, script: str, content: bytes):
        """
        Saves the script with the provided content.
        """
        # Save a script locally.
        destination_script_path = cls.to_destination_local_path(script)
        destination_script_absdir = pathlib.Path(destination_script_path).parent
        os.makedirs(destination_script_absdir, exist_ok=True)
        
        if not os.path.isfile(destination_script_path):
            # file doesnt exist, create file.
            with open(destination_script_path, 'ab'):
                pass
        
        with open(destination_script_path, 'wb') as fd:
            fd.write(content)
    
    @classmethod
    def download_missing_remote_scripts(cls, scripts: List[str]):
        """
        Downloads remote scripts and save them to destination scripts directory.
        """      
        def save_script(script, content):
            """
            Saves the script with the provided content.
            """
            cls.save_script(script, content)
            console.log_raw(f"Script '{script}' successfully downloaded!", custom_color=console.Fore.GREEN)
            
        for script in scripts:
            if is_absolute_url(script):
                # This is a remote script, lets download it.
                response = requests.get(script, timeout=1)
                status_code = response.status_code
                
                if status_code != 200:
                    # Unexpected response
                    console.log_raw(f"Received unexpected status code for script '{script}' [{response.status_code}]")
                else:
                    # Save script locally
                    save_script(script, response.content)
            else:
                # Script unexpected, expected a remote script but got a local script instead.
                console.log_raw(f"Skipping, expected a remote url but got: {script}", custom_color=console.Fore.YELLOW)
