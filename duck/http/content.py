"""
Module to represent a request/response Content class.
"""
import gzip
import zlib
import fnmatch
from typing import Tuple

from duck.exceptions.all import ContentError
from duck.http.mimes import (
    guess_data_mimetype,
    guess_file_mimetype,
)
from duck.settings import SETTINGS


CONTENT_COMPRESSION = SETTINGS["CONTENT_COMPRESSION"]

COMPRESSION_ENCODING = CONTENT_COMPRESSION.get(
    "encoding", "identity",
)  # defaults to gzip
    
COMPRESSION_MIN_SIZE = CONTENT_COMPRESSION.get(
    "min_size", 1024,
)  # defaults to files more than 1KB

COMPRESSION_MAX_SIZE = CONTENT_COMPRESSION.get(
    "max_size", 512 * 1024,
)  # defaults to files not more than 512KB
    
COMPRESSION_LEVEL = CONTENT_COMPRESSION.get(
    "level", 5,
)  # defaults to 5, optimum in most cases

COMPRESS_STREAMING_RESPONSES = CONTENT_COMPRESSION.get(
    "compress_streaming_responses", True,
)  # defaults to True

COMPRESSION_MIMETYPES = CONTENT_COMPRESSION.get(
    "mimetypes",
    [
        "text/*",
        "application/javascript",
        "application/json",
        "application/xml",
        "application/xhtml+xml",
        "application/rss+xml",
        "application/atom+xml",
    ],  # avoid compressing already compressed files like images
)


class Content:
    """
    Content class to represent the data to be sent in the response.
    """
    __slots__ = (
        "_Content__data",
        "_Content__filepath",
        "_Content__encoding",
        "_Content__content_type",
        "_force_size",
        "compression_min_size",
        "compression_max_size",
        "compression_level",
        "compression_mimetypes",
        "supported_encodings",
        "suppress_errors",
        "auto_read_file",
    )
    
    def __init__(
        self,
        data: bytes = b"",
        filepath: str = None,
        content_type: str = None,
        encoding: str = "identity",
        compression_min_size: int = COMPRESSION_MIN_SIZE,
        compression_max_size: int = COMPRESSION_MAX_SIZE,
        compression_level: int = COMPRESSION_LEVEL,
        compression_mimetypes: list = COMPRESSION_MIMETYPES,
        suppress_errors: bool = False,
        auto_read_file: bool = True,
    ):
        """
        Initialize the content object.

        Args:
            data (bytes): The data to be set.
            filepath (str): The file path to read data from.
            content_type (str): The content type of the data.
            encoding (str): The encoding of the data.
            compression_min_size (int): The minimum size of data to compress.
            compression_max_size (int): The maximum size of data to compress.
            compression_level (int): The compression level to use.
            compression_mimetypes (list): The list of mimetypes to compress.
            suppress_errors (bool): Whether to suppress errors by trying to fix any issues.
            auto_read_file (bool): Automatically read file and set as data if data not provided.
        """
        self.__data = None
        self.__filepath = None
        self.__encoding = None
        self.__content_type = None
        self._force_size = None
        self.compression_min_size = compression_min_size
        self.compression_max_size = compression_max_size
        self.compression_level = compression_level
        self.compression_mimetypes = compression_mimetypes
        self.supported_encodings = ["gzip", "deflate", "identity", "br"]
        self.suppress_errors = suppress_errors
        self.auto_read_file = auto_read_file
        self.set_content(data or b'', filepath, content_type)
        self.encoding = encoding

    def _compress(self, data: bytes, encoding: str, **kwargs) -> Tuple[bytes, bool]:
        """
        Compress data for the provided encoding.

        Args:
            data (bytes): The data to compress.
            encoding (str): The encoding to use.
            **kwargs: Additional arguments for zlib, brotli or deflate compression

        Returns:
            (data, success) (Tuple[bytes, bool]): The data and bool whether compression was successful.

        Conditions:
         - `enable_content_compression` = True.
         - `size` <= compression_max_size and `size` >= compression_min_size
         - `content_type` set.
         - `encoding` is recognized.
         - `data` is in bytes.
        """
        success = False
        
        mimetype_supported = self.mimetype_supported(self.content_type)
        
        if (data and len(data) <= self.compression_max_size
                and len(data) >= self.compression_min_size
                and isinstance(data, bytes) and mimetype_supported):
            
            if not encoding:
                raise ContentError(
                    "Please set encoding first to compress data")

            if encoding == "gzip":
                data = gzip.compress(data, compresslevel=self.compression_level)
                success = True
            
            elif encoding == "deflate":
                data = zlib.compress(data, level=self.compression_level, **kwargs)
                success = True
            
            elif encoding == "br":
                try:
                    import brotli
                except ImportError as e:
                    raise ContentError(
                        "Brotli compression requires brotli library, please install it first using `pip install brotli`"
                    ) from e
                data = brotli.compress(data, quality=self.compression_level, **kwargs)
                success = True
            
            elif encoding == "identity":
                success = True
        return data, success

    def _decompress(self, data: bytes) -> Tuple[bytes, bool]:
        """
        Decompress data for the provided encoding.

        Returns:
            (data, success) (Tuple[bytes, bool]): The data and bool whether decompression was successful.

        Conditions:
        - `enable_content_compression` = True.
        - `content_type` set.
        - `size` <= compression_max_size
        - `encoding` is recognized.
        - `data` is in bytes.
        """
        success = False
        
        mimetype_supported = self.mimetype_supported(self.content_type)
        
        if (data and len(data) <= self.compression_max_size
                and isinstance(data, bytes) and mimetype_supported):
            
            if not self.encoding:
                raise ContentError(
                    "Please set encoding first to decompress data")

            if self.encoding == "gzip":
                data = gzip.decompress(data)
                success = True
            
            elif str(self.encoding).lower() == "deflate":
                data = zlib.decompress(data)
                success = True
            
            elif self.encoding == "br":
                try:
                    import brotli
                except ImportError as e:
                    raise ContentError(
                        "Brotli decompression requires brotli library, please install it first using `pip install brotli`"
                    ) from e
                data = brotli.decompress(data)
                success = True
            
            elif self.encoding == "identity":
                success = True
        return data, success

    def mimetype_supported(self, mimetype: str) -> bool:
        """
        Checks whether the given mimetype is supported for compression or decompression.
        """
        for pattern in self.compression_mimetypes:
            if fnmatch.fnmatch(mimetype, pattern):
                return True
        return False
        
    def correct_encoding(self):
        """
        Returns the calculated current correct encoding depending on the current data.
        """
        if not self.data:
            return "identity"

        if self.data.startswith(b"\x1f\x8b\x08"):
            return "gzip"

        if (self.data.startswith(b"\x78\x9c")
                or self.data.startswith(b"\x78\x01")
                or self.data.startswith(b"\x78\xda")):
            return "deflate"

        if self.data.startswith(b"\x8b\x8b\x8b"):
            return "br"

        return "identity"

    @property
    def compressed(self):
        """
        Check if the content data is compressed.
        """
        if self.correct_encoding() != "identity":
            return True
        return False

    def compress(self, encoding: str, **kwargs) -> bool:
        """
        Compress the content data.

        Args:
            encoding (str): The encoding to use.
            **kwargs: Additional arguments for zlib, brotli or deflate compression

        Returns:
            bool: Whether compression has been successfull.
        """
        if not self.data:
            return self.data, False

        self.data, success = self._compress(self.data, encoding, **kwargs)

        if success:
            self.__encoding = encoding

        return success

    def decompress(self):
        """
        Decompress the content data.

        Returns:
            bool: Whether compression has been successfull.
        """
        if not self.data:
            self.__encoding = "identity"
            return self.data, False

        self.data, success = self._decompress(self.data)

        if success:
            self.__encoding = "identity"

        return success

    @property
    def raw(self):
        return self.data

    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, data: bytes):
        if not isinstance(data, bytes):
            if self.suppress_errors:
                self.__data = b""
                return self.__data
            raise ContentError("Bytes required as data.")
        self.__data = data
        return self.__data

    @property
    def filepath(self) -> str:
        """
        Get the file path.
    
        Returns:
            str: The current file path.
        """
        return self.__filepath
    
    @filepath.setter
    def filepath(self, filepath: str) -> None:
        """
        Set the file path.
    
        Args:
            filepath (str): The new file path to set.
        """
        self.__filepath = filepath
    
    @property
    def encoding(self) -> str:
        """
        Get the file encoding.
    
        Returns:
            str: The current encoding of the file.
        """
        return self.__encoding
    
    @encoding.setter
    def encoding(self, encoding: str) -> None:
        """
        Set the file encoding.
    
        Args:
            encoding (str): The new encoding to set.
        """
        self.__encoding = encoding
    
    @property
    def content_type(self) -> str:
        """
        Get the content type.
    
        Returns:
            str: The current content type.
        """
        return self.__content_type
    
    @content_type.setter
    def content_type(self, content_type: str) -> None:
        """
        Set the content type.
    
        Args:
            content_type (str): The new content type to set.
        """
        self.__content_type = content_type

    @property
    def size(self) -> int:
        """
        Returns the size of the data. 
        If a fake size is set, it returns the forced size. 
        Otherwise, it calculates the size based on the current data.
        """
        if self._force_size is not None:
            return self._force_size
        if self.__data is not None:
            return len(self.__data)
        return 0
    
    def set_fake_size(self, size: int) -> None:
        """
        Forcefully set a fake size for the data.
    
        Args:
            size (int): The fake size to set.
        """
        self._force_size = size
    
    def remove_fake_size(self) -> None:
        """
        Remove the forced fake size, restoring size calculation 
        to be based on the actual data.
        """
        self._force_size = None
        
    def parse_type(self, content_type=None):
        """
        Parse the mimetype of content data, if content_type is None, the content_type will be guessed.
        """
        if not content_type:
            if self.filepath:
                content_type = guess_file_mimetype(self.filepath)
            
            # guess data mimetype if guessing filedata mimetype fails
            content_type = content_type or guess_data_mimetype(
                data=self.data or b"")

            if not content_type:
                # guessing data and filedata mimetype fails, this is likely binary content
                content_type = "application/octet-stream"
        self.content_type = content_type

    def set_content(
        self,
        data: bytes = b"",
        filepath: str = None,
        content_type=None,
    ):
        """
        Set the content and data should already be encoded to bytes.
        """
        if not data:
            if filepath and self.auto_read_file:
                try:
                    with open(filepath, "rb") as fd:
                        data = fd.read()
                except Exception as e:
                    if self.suppress_errors:
                        self.__data = b""
                        return
                    raise ContentError(
                        f"Could not set content from file {filepath}: {e}"
                    ) from e
        self.filepath = filepath
        self.data = bytes(data, "utf-8") if not isinstance(data, bytes) else data
        self.parse_type(content_type=content_type)
        
    def __repr__(self):
        return f"<{self.__class__.__name__} encoding={self.encoding}, size={self.size}, content_type={self.content_type}, compressed={self.compressed}>"
