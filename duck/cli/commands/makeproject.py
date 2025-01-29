"""
Module containing makeproject command class.
"""
import os

from duck.logging import console


class MakeProjectCommand:
    # makeproject command
    
    @classmethod
    def setup(cls):
        # Setup before command execution
        os.environ.setdefault("DUCK_SETTINGS_MODULE", "duck.etc.structures.projects.testing.settings")
    
    @classmethod
    def main(
        cls,
        name,
        dest_dir: str = ".",
        overwrite_existing: bool = False,
        project_type: str = "normal"
     ):
        # Setup minimum settings module for CLI to function correctly
        cls.setup()
        cls.makeproject(name, dest_dir, overwrite_existing, project_type)
    
    @classmethod
    def makeproject(
        cls,
        name,
        dest_dir: str = ".",
        overwrite_existing: bool = False,
        project_type: str = "normal",
     ):
        # Execute command after setup.
        from duck.setup.makeproject import makeproject
        
        dest_dir = os.path.abspath(dest_dir)
        
        console.log(
            f'Creating Duck {project_type.title()} Project' if project_type != "normal"
            else f'Creating Duck Project',
            level=console.DEBUG,
        )
        try:
            makeproject(
                name,
                dest_dir,
                overwrite_existing=overwrite_existing,
                project_type=project_type,
            )  # create project
            
            # Log something to the console
            console.log(
                f'Project "{name}" created in directory "{dest_dir}"',
                custom_color=console.Fore.GREEN,
            )
        except FileExistsError:
            console.log(
                f'Project with name "{name}" already exists in destination directory: {dest_dir}',
                level=console.WARNING,
            )
            overwrite = input(
                "\nDo you wish to overwrite the existing project (y/N): ")
    
            print() # print a newline
    
            if overwrite.lower().startswith("y"):
                makeproject(
                    name,
                    dest_dir,
                    overwrite_existing=True,
                    project_type=project_type)
                
                # Log something to console.
                console.log(
                    f'Project "{name}" created in directory "{dest_dir}"',
                    custom_color=console.Fore.GREEN)
            else:
                console.log("Cancelled project creation!", level=console.DEBUG)
    
        except Exception as e:
            # Project creation failed.
            console.log(f"Error: {str(e)}", level=console.ERROR)
            raise e
        