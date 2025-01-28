"""
File Management Utilities Module

Provides utility functions for file operations such as reading, writing, renaming,
moving, and deleting files.
"""
import os
import shutil


def read_file(file_path: str) -> str:
    """
    Reads the contents of a file.
    
    Args:
        file_path (str): The file path to read from.
    
    Returns:
        str: The contents of the file.
    """
    with open(file_path, 'r') as file:
        return file.read()


def write_to_file(file_path: str, data: str) -> None:
    """
    Writes data to a file.
    
    Args:
        file_path (str): The file path to write to.
        data (str): The data to write.
    """
    with open(file_path, 'w') as file:
        file.write(data)


def move_file(source: str, destination: str) -> None:
    """
    Moves a file from the source path to the destination path.
    
    Args:
        source (str): The source file path.
        destination (str): The destination file path.
    """
    shutil.move(source, destination)


def delete_file(file_path: str) -> None:
    """
    Deletes a file.
    
    Args:
        file_path (str): The file path to delete.
    """
    if os.path.exists(file_path):
        os.remove(file_path)
