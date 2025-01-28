"""
This module provides a simple inter-process communication (IPC) mechanism using file streams.
It allows processes to communicate by writing to and reading from a shared file.

Functions:
    get_writer() -> FileWriter: Returns a FileWriter object for writing messages.
    get_reader() -> FileReader: Returns a FileReader object for reading messages.
    
Example Usage:
    # Process 1
    with get_writer() as writer:
        writer.write_message('Hello from Process 1')
    
    # Process 2
    with get_reader() as reader:
        message = reader.read_message()
        print(message)
"""

import os


class FileWriter:
    """
    A class to write messages to a shared file for IPC.
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.file = None
        if not self.file:
            self.__enter__()  # Open the file

    def __enter__(self):
        if not self.file:
            self.file = open(self.filepath, "w")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def write_message(self, message: str):
        """
        Write a message to the file.

        Args:
            message (str): The message to write.
        """
        self.file.write(message + "\n")
        self.file.flush()

    def close(self):
        """
        Close the file.
        """
        if self.file:
            self.file.close()


class FileReader:
    """
    A class to read messages from a shared file for IPC.
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.file = None
        if not self.file:
            self.__enter__()  # Open the file

    def __enter__(self):
        if not self.file:
            self.file = open(self.filepath, "r")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def read_message(self) -> str:
        """
        Read a message from the file.

        Returns:
            str: The message read from the file.
        """
        self.file.seek(0)
        return self.file.readline().strip()

    def close(self):
        """
        Close the file.
        """
        if self.file:
            self.file.close()


def get_writer(filepath: str = ".ipc") -> FileWriter:
    """
    Get a FileWriter object for writing messages.

    Args:
        filepath (str): The path to the shared file. Defaults to 'ipc_file.txt'.

    Returns:
        FileWriter: The FileWriter object.
    """
    if not os.path.isfile(filepath):
        with open(filepath, "x"):
            pass  # Create the file if it doesn't exist
    return FileWriter(filepath)


def get_reader(filepath: str = ".ipc") -> FileReader:
    """
    Get a FileReader object for reading messages.

    Args:
        filepath (str): The path to the shared file. Defaults to 'ipc_file.txt'.

    Returns:
        FileReader: The FileReader object.
    """
    if not os.path.isfile(filepath):
        with open(filepath, "x"):
            pass  # Create the file if it doesn't exist
    return FileReader(filepath)
