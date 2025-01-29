"""
Module for creating blueprint directory structure.
"""

import os
import shutil

from pathlib import Path

from duck.utils.path import joinpaths
from duck.logging import console
from duck.storage import duck_storage


BLUEPRINT_TEMPLATE = """
from duck.routes import Blueprint
from duck.urls import path, re_path

from . import views

{blueprint_name} = Blueprint(
    location=__file__,
    name="{blueprint_name_lower}",
    urlpatterns=[
        # URL patterns here
    ],
    prepend_name_to_urls=False,
    enable_static_dir=True,
    enable_template_dir=True,
    static_dir="static",
)
"""

def ignore_pycache(dir_path, contents):
    """
    Ignore __pycache__ directories during copy.
    """
    # Exclude any __pycache__ directories
    return {
        name
        for name in contents
        if (Path(dir_path) / name).is_dir() and name == "__pycache__"
    }


def create_blueprint_py(blueprint_name: str, dest_directory):
    """
    Creates a blueprint.py file in provided directory for the provided blueprint.
        
    Args:
        blueprint_name (str): The blueprint name.
        dest_directory (str): The destination directory.
    """
    blueprint_path = joinpaths(dest_directory, 'blueprint.py')
    
    with open(blueprint_path, "a"):
        # create file if it doesn't extist
        pass
        
    with open(blueprint_path, "w") as f:
        f.write(
            BLUEPRINT_TEMPLATE.format(
                blueprint_name=blueprint_name,
                blueprint_name_lower=blueprint_name.lower()
        ))


def makeblueprint(
    name: str,
    base_dir: str,
    overwrite_existing: bool = False,
) -> None:
    """
    Create a Duck blueprint directory structure in provided base_dir.
    """
    if not name:
        raise TypeError("Please provide a name for blueprint (preferrebly TitleCase)")
        
    blueprint_dir = joinpaths(duck_storage, f"etc/structures/blueprint")
    destination_dir = os.path.join(base_dir, name.lower())

    if overwrite_existing:
        # Overwrite existing project.
        try:
            shutil.rmtree(destination_dir)
        except:
            pass
            
    # Copy project structure
    shutil.copytree(
         blueprint_dir,
         destination_dir,
         dirs_exist_ok=overwrite_existing,
         ignore=ignore_pycache,
     )
    
    if os.path.isdir(destination_dir):
        if overwrite_existing:
            create_blueprint_py(name, destination_dir)
    else:
        create_blueprint_py(name, destination_dir)
