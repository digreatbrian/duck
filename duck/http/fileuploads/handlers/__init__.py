"""
Module containing classes for storing uploaded file data.
"""

import io
import os

from duck.settings import SETTINGS
from duck.utils.object_mapping import map_data_to_object


class FileUploadError(Exception):
    """
    Base exception class for file upload errors
    """


class BaseFileUpload(io.BytesIO):
    """
    Base class for storing file uploads data.

    Attributes:
        initial_bytes (bytes): The initial byte content of the file.
        filename (str): The name of the file.
    """

    def __init__(self, filename: str, initial_bytes: bytes = b"", **kw):
        self.initial_bytes = initial_bytes
        self.filename = filename

        assert filename or False, "Filename is required"

        if not isinstance(initial_bytes, bytes):
            raise FileUploadError(f"Bytes required not {type(initial_bytes)}")

        super().__init__(initial_bytes)

        # Map additional keyword arguments to instance attributes
        map_data_to_object(self, kw)

    def save_to_file(self, filepath: str):
        """
        Save the uploaded data to a file.

        Args:
            filepath (str): The path where the file will be saved.

        Returns:
            int: The number of bytes written.
        """
        with open(filepath, "wb") as f:
            return f.write(self.getvalue())

    def save(self):
        """
        Save the uploaded data. This method should be implemented by subclasses.

        Raises:
            NotImplementedError: If the method is not implemented by subclasses.
        """
        raise NotImplementedError(
            "Implementation of the method 'save' is required")

    def __repr__(self):
        r = f"<{self.__class__.__name__} {self.filename}"
        if hasattr(self, "content_type"):
            r += f" ({self.content_type})>"
        else:
            r += ">"
        return r


class TemporaryFileUpload(BaseFileUpload):
    """
    Class for temporarily storing file upload data in memory.
    """

    def save(self):
        """
        Save the uploaded data. In this case, the method does nothing.
        """


class PersistentFileUpload(BaseFileUpload):
    """
    Class for persistent storage of file uploads on disk in a specified directory.

    Attributes:
        filename (str): The name of the file.
        initial_bytes (bytes): The initial byte content of the file.
        directory (str): The directory where the file will be saved.
        overwrite_existing_file (bool): Whether to overwrite existing file in directory when saving
    """

    def __init__(
        self,
        filename: str,
        initial_bytes: bytes = b"",
        directory: str = SETTINGS["FILE_UPLOAD_DIR"],
        overwrite_existing_file=True,
        **kw,
    ):
        self.initial_bytes = initial_bytes
        self.directory = directory
        self.filename = filename
        self.overwrite_existing_file = overwrite_existing_file

        if not os.path.isdir(directory):
            raise FileNotFoundError(f"Directory {directory} does not exist")

        if not filename:
            raise FileUploadError(
                f"Please provide filename, should not be '{filename}' ")

        self.filepath = os.path.join(directory, filename)

        if os.path.isfile(self.filepath) and not overwrite_existing_file:
            raise FileUploadError(
                "File '{self.filepath}' already exists and argument 'overwrite_existing_file' is not True "
            )

        super().__init__(filename, initial_bytes, **kw)

    def save_to_file(self):
        """
        Save the uploaded data to the specified file path.

        Returns:
            int: The number of bytes written.
        """
        return super().save_to_file(self.filepath)

    def save(self):
        """
        Save the uploaded data by writing it to the specified file path.
        """
        self.save_to_file()
