"""
Module containing collectstatic command class.
"""
import shutil
import pathlib
from typing import List, Generator, Tuple

from duck.routes import Blueprint
from duck.utils.path import joinpaths


class CollectStaticCommand:
    # collectstatic command
    
    @classmethod
    def setup(cls):
        pass
        
    @classmethod
    def main(cls, skip_confirmation: bool = False):
        cls.setup()
        cls.collectstatic(skip_confirmation)
    
    @classmethod
    def collectstatic(cls, skip_confirmation: bool = False) -> None:
        # Execute command after setup.
        from duck.settings import SETTINGS
        
        static_root = str(SETTINGS["STATIC_ROOT"])
        
        blueprint_static_dirs: List[str, Blueprint] = list(cls.find_blueprint_static_dirs())
        blueprint_staticfiles: List[str] = list(cls.get_blueprint_staticfiles(blueprint_static_dirs))
        blueprint_staticfiles_len = len(blueprint_staticfiles)
    
        if blueprint_staticfiles_len == 0:
            console.log_raw("\nNo staticfiles found!", level=console.WARNING)
            return
    
        if not skip_confirmation:
            # Show confirmation prompt
            console.log_raw(
                f"\nWould you like to copy {blueprint_staticfiles_len} staticfile(s) to {static_root} (y/N): ",
                end="",
                level=console.DEBUG)
            
            # Obtain confirmation from console.
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
            custom_color=console.Fore.GREEN)
        
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
