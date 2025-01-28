"""
Module for creating project structure.
"""

import os
import shutil
from pathlib import Path
from duck.utils.path import joinpaths
from duck.storage import duck_storage


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


def makeproject(
    name: str,
    base_dir: str = ".",
    overwrite_existing: bool = False,
    project_type: str = "normal",
) -> None:
    """
    Create a Duck project in provided base_dir.
    """
    if not name:
        raise TypeError("Please provide a name for makeproject")

    if not os.path.isdir(base_dir):
        raise FileNotFoundError(
            "Base directory does'nt exist, make sure you provided the correct path"
        )
    
    # Validate project type
    assert bool(
        project_type in ["normal", "full", "mini"]
    ), "Invalid project type, should be one of ['normal', 'full', 'mini']."

    project_dir = joinpaths(duck_storage, f"etc/structures/projects/{project_type}")
    destination_dir = joinpaths(base_dir, name)

    if overwrite_existing:
        # Overwrite existing project.
        try:
            shutil.rmtree(destination_dir)
        except:
            pass
    
    # Copy project structure
    shutil.copytree(
        project_dir,
        destination_dir,
        dirs_exist_ok=overwrite_existing,
        ignore=ignore_pycache,
    )
