"""
Module containing extra Duck CLI commands.
"""
import os
import shutil
import pathlib
import argparse
import urllib.parse
from typing import Generator, Tuple, List

from duck.routes import Blueprint
from duck.utils.path import (
    is_absolute_url,
    joinpaths,
)


def create_temp_settings_py(directory: str = "."):
    """
    Creates temporary empty settings.py file.
    """
    file = joinpaths(directory, "settings.py")
    if not os.path.isfile(file):
        with open(file, "a"):
           pass


def remove_temp_settings_py(directory: str = "."):
    """
    Removes temporary empty settings.py file.
    """
    file = joinpaths(directory, "settings.py")
    if os.path.isfile(file):
        with open(file, "r") as fd:
            if not fd.read():
                os.unlink(file)  # remove file if empty.


class CollectStaticCommand:
    """
    CollectStaticCommand class representing the collectstatic command.
    """
    @classmethod
    def main(cls, parsed_args: argparse.Namespace) -> None:
        """
        Collects staticfiles from all blueprint base directories and place them in one static directory grouped by name.
    
        Args:
            parsed_args (argparse.Namespace): Parsed arguments from the command line.
        """
        # Create temporary settings file to avoid SettingsError. (if necessary)
        create_temp_settings_py()
    
        from duck.logging import console
        from duck.settings import SETTINGS
        
        static_root = str(SETTINGS["STATIC_ROOT"])
        
        try:
            blueprint_static_dirs: List[str, Blueprint] = list(cls.find_blueprint_static_dirs())
            blueprint_staticfiles: List[str] = list(cls.get_blueprint_staticfiles(blueprint_static_dirs))
            blueprint_staticfiles_len = len(blueprint_staticfiles)
    
            if blueprint_staticfiles_len == 0:
                console.log_raw("\nNo staticfiles found!", level=console.WARNING)
                return
    
            if not parsed_args.skip_confirmation:
                console.log_raw(
                    f"\nWould you like to copy {blueprint_staticfiles_len} staticfile(s) to {static_root} (y/N): ",
                    end="",
                    level=console.DEBUG,
                )
                
                choice = input("")
                
                if not choice.lower().startswith("y"):
                    console.log_raw("\nCancelled, bye!", level=console.WARNING)
                    return
    
            for static_dir, blueprint in blueprint_static_dirs:
                dst = joinpaths(
                    static_root,
                    blueprint.name,
                    blueprint.static_dir,
                )
                shutil.copytree(static_dir, dst, dirs_exist_ok=True)
    
            console.log_raw(
                f"\nSuccessfully copied {blueprint_staticfiles_len} staticfile(s) to {static_root}",
                custom_color=console.Fore.GREEN,
            )
        finally:
            # Remove temp settings.py if it has been created in the first place.
            remove_temp_settings_py()
    
    @classmethod
    def recursive_getfiles(cls, directory: str) -> str:
       """
       Returns a generator for all files and subfiles within the directory.
       """
       directory = pathlib.Path(directory)
       
       if directory.is_dir():
           for dir_entry in directory._scandir():
                if dir_entry.is_file():
                    yield dir_entry.path
                else:
                    for i in cls.recursive_getfiles(dir_entry.path):
                        yield i
    
    @classmethod
    def find_blueprint_static_dirs(cls) -> Generator:
        """
        Finds and returns static directories from all blueprint base directories.
    
        Returns:
            Generator: The generator of static directory and blueprint pair.
        """
        from duck.settings.loaded import BLUEPRINTS
        
        for blueprint in BLUEPRINTS:
            if blueprint.enable_static_dir:
                # access to to blueprint static files is allowed.
                static_dir = joinpaths(
                    blueprint.root_directory,
                    blueprint.static_dir,
                )
                if pathlib.Path(static_dir).is_dir():
                     yield (static_dir, blueprint)
    
    @classmethod
    def get_blueprint_staticfiles(cls, blueprint_static_dirs: Tuple[str, Blueprint]):
        """
        Returns the generator to the found staticfiles.
        
        Args:
            blueprint_static_dirs (Tuple[str, Blueprint]): The collection of the static directory and the respective blueprint.
        """
        for static_dir, blueprint in blueprint_static_dirs:
            for static_file in cls.recursive_getfiles(static_dir):
                yield static_file
        

class CollectScriptsCommand:
    """
    CollectScriptsCommand class representing the collectscripts command.
    """
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
        return joinpaths(
            cls.static_root,
            "react_fronted/scripts",
         )
    
    @classmethod
    def to_destination_local_path(cls, script: str):
        """
        Returns the destination local path for the provided script.
        
        Args:
            script (str): Local path or remote url for the script e.g ./scripts/script.js or https://some.site/script.js
        """
        parse_result = urllib.parse.urlparse(script)
        
        if not parse_result.scheme:
             # script is a local path.
             destination_script_path = joinpaths(cls.destination_dir, script.lstrip("."))
        else:
             # script is a remote url.
             destination_script_path = joinpaths(cls.destination_dir, script.split("://", 1)[-1])
        return destination_script_path
        
    @classmethod
    def main(cls, parsed_args: argparse.Namespace) -> None:
        """
        Collects scripts in FRONTEND and save them locally.
    
        Args:
            parsed_args (argparse.Namespace): Parsed arguments from the command line.
        """
        create_temp_settings_py()  # Create temp settings file to avoid SettingsError. (if necessary)
        
        from duck.settings.loaded import FRONTEND
        from duck.logging import console
        
        try:
            if not FRONTEND:
                console.log_raw(
                    "Fronted configuration for React not set, ensure the variable FRONTEND is set correctly in settings.py and try again.",
                    level=console.WARNING
                )
                return
            
            scripts = FRONTEND["REACT"]["scripts"]
            missing_remote_scripts = [] # local scripts missing in local destination directory.
            missing_local_scripts = [] # local scripts missing in local destination directory.
            
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
                     if not parsed_args.skip_confirmation:
                         console.log_raw(
                             f"Would you like to copy {len(missing_local_scripts)} missing script(s) (y/N): ",
                             level=console.DEBUG,
                             end="",
                          )
                         choice = input("")
                         if choice.lower().startswith('y'):
                             cls.copy_missing_local_scripts(missing_local_scripts)
                         else:
                             console.log_raw("Skipped copy of local missing scripts!", custom_color=console.Fore.YELLOW)
                             console.log_raw(f"\nScripts: {missing_local_scripts}", custom_color=console.Fore.YELLOW)
                     else:
                         cls.copy_missing_local_scripts(missing_local_scripts)
                 
                 if missing_remote_scripts:
                     if not parsed_args.skip_confirmation:
                         console.log_raw(
                             f"\nWould you like to download {len(missing_remote_scripts)} missing script(s) (y/N): ",
                             level=console.DEBUG,
                             end="",
                          )
                         choice = input("")
                         if choice.lower().startswith('y'):
                             cls.download_missing_remote_scripts(missing_remote_scripts)
                         else:
                             console.log_raw("Skipped download of missing remote scripts!", custom_color=console.Fore.YELLOW)
                             console.log_raw(f"\nScripts: {missing_remote_scripts}", custom_color=console.Fore.YELLOW)
                     else:
                         cls.download_missing_remote_scripts(missing_remote_scripts)
            else:
                if not scripts:
                    console.log_raw("Nothing to collect, scripts are empty!", level=console.WARNING)
                else:
                    console.log_raw("Nothing to collect, script(s) seem to be locally available!", level=console.WARNING)
        finally:
            # Remove temp settings.py if it has been created in the first place.
            remove_temp_settings_py()
    
    @classmethod
    def copy_missing_local_scripts(cls, scripts: List[str]):
        """
        Copies local missing scripts to the destination scripts directory.
        """
        from duck.logging import console
        
        def save_script(script, content):
            """
            Saves the script with the provided content.
            """
            cls.save_script(script, content)
            console.log_raw(f"Script '{script}' successfully copied!", custom_color=console.Fore.GREEN)
        
        for script in scripts:
            if is_absolute_url(script):
                console.log_raw(f"Skipping, expected a local file but got a remote url: {script}")
                continue
            
            if not os.path.isfile(script):
                raise FileNotFoundError(f"Script '{script}' is required but cannot be found")
            
            with open(script, "rb") as fd:
                save_script(script, fd.read())
            
    @classmethod
    def save_script(cls, script: str, content: bytes):
        """
        Saves the script with the provided content.
        """
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
        Downloads remote scripts and copies them to destination scripts directory.
        """
        import requests
        from duck.logging import console
        
        def save_script(script, content):
            """
            Saves the script with the provided content.
            """
            cls.save_script(script, content)
            console.log_raw(f"Script '{script}' successfully downloaded!", custom_color=console.Fore.GREEN)
            
        for script in scripts:
            if is_absolute_url(script):
                response = requests.get(script, timeout=1)
                status_code = response.status_code
                if  status_code != 200:
                    console.log_raw(f"Received unexpected status code for script '{script}' [{response.status_code}]")
                else:
                    save_script(script, response.content)
            else:
                console.log_raw(f"Skipping, expected a remote url but got: {script}", custom_color=console.Fore.YELLOW)
                continue


class MakeBlueprintCommand:
    """
    MakeBlueprintCommand class representing the makeblueprint command.
    """
    @classmethod
    def main(cls, parsed_args: argparse.Namespace) -> None:
        """
         Creates a blueprint with necessary files and directories.
    
        Args:
            parsed_args (argparse.Namespace): Parsed arguments from the command line.
        """
        # Create temporary settings file to avoid SettingsError. (if necessary)
        create_temp_settings_py()
        
        from duck.logging import console
        from duck.setup.makeblueprint import makeblueprint
        
        name = parsed_args.args[0]
        destination_dir = parsed_args.dest or "."
        destination_dir = os.path.abspath(destination_dir)
        overwrite = parsed_args.overwrite
        
        # Log something
        console.log(f'Creating Awesome Duck Blueprint', level=console.DEBUG)
        
        try:
            makeblueprint(
                name,
                destination_dir,
                overwrite_existing=bool(overwrite),
            )  # create blueprint directory structure
            
            # Log msg on blueprint creation.
            console.log(
                f'Blueprint "{name}" created in directory "{destination_dir}"',
                custom_color=console.Fore.GREEN,
            )
        except FileExistsError:
            # Blueprint already exists
            console.log(
                f'Blueprint with name "{name}" already exists in destination directory: {destination_dir}',
                level=console.WARNING,
            )
            overwrite = input(
                "\nDo you wish to overwrite the existing blueprint (y/N): ")
    
            print()
    
            if overwrite.lower().startswith("y"):
                makeblueprint(
                    name,
                    destination_dir,
                    overwrite_existing=True,
                    project_type=project_type,
                 )
                console.log(
                    f'Blueprint "{name}" created in directory "{destination_dir}"',
                    custom_color=console.Fore.GREEN,
                )
            else:
                console.log("Cancelled project creation!", level=console.DEBUG)
    
        except Exception as e:
            console.log(f"Error: {str(e)}", level=console.ERROR)
            raise e
    
        finally:
            remove_temp_settings_py(
            )  # remove temp settings.py if it has been created in the first place.
    