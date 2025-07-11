"""
Module containing makeproject command class.
"""
import os

from duck.logging import console
from duck.routes import Blueprint
from duck.utils.urlcrack import URL
from duck.utils.path import joinpaths


class MakeBlueprintCommand:
    # makeblueprint command
    
    @classmethod
    def setup(cls):
        pass
        
    @classmethod
    def main(
        cls,
        name,
        destination: str = '.',
        overwrite_existing: bool = False,
     ):
        cls.setup()
        cls.makeblueprint(name, destination, overwrite_existing)
        
    @classmethod
    def makeblueprint(cls,
        name,
        destination,
        overwrite_existing: bool = False,
     ):
        from duck.settings import SETTINGS
        from duck.setup.makeblueprint import makeblueprint
        
        dest_dir = os.path.abspath(destination)
        dest_blueprint_path = joinpaths(dest_dir, name)
        
        # Log something
        console.log(f'Creating "{name}" Duck Blueprint', level=console.DEBUG)
        
        try:
            makeblueprint(
                name,
                dest_dir,
                overwrite_existing=overwrite_existing,
            )  # create blueprint directory structure
            
            # Log msg on blueprint creation.
            console.log(
                f'Blueprint "{name}" created in directory "{dest_dir}"',
                custom_color=console.Fore.GREEN,
            )
        except FileExistsError:
            # Blueprint already exists
            console.log(
                f'Blueprint with name "{name}" already exists in destination directory: {dest_dir}',
                level=console.WARNING,
            )
            
            # Get confirmation on whether to overwrite existing blueprint.
            overwrite = input("\nDo you wish to overwrite the existing blueprint (y/N): ")
    
            # Print a newline for better output
            print()
    
            if overwrite.lower().startswith("y"):
                # Overwrite existing blueprint
                makeblueprint(
                    name,
                    dest_dir,
                    overwrite_existing=True,
                 )
                
                # Log success message
                console.log(
                    f'Blueprint "{name}" created at "{dest_blueprint_path}"',
                    custom_color=console.Fore.GREEN,
                )
            else:
                # Blueprint creation cancelled
                console.log("Cancelled blueprint creation!", level=console.DEBUG)
    
        except Exception as e:
            # Error creating blueprint.
            console.log(f"Error: {str(e)}", level=console.ERROR)
            raise e
