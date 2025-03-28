"""
BytesMultiPartParser Module

This module provides the BytesMultiPartParser class, which is designed to parse 
multipart form-data, particularly from raw bytes input. It is useful for handling 
file uploads or form submissions where the data is received in a multipart format.

Classes:
- `BytesMultiPartParser`: A parser for multipart form-data.

Exceptions:
- `MultiPartParserError`: Raised when parsing errors occur.

Usage Example:

```py
headers = {
    'Content-Type': b'multipart/form-data; boundary=---------------------------354901075210407969363875912417'
}
input_data = b'''-----------------------------354901075210407969363875912417
Content-Disposition: form-data; name="field1"

value1
-----------------------------354901075210407969363875912417
Content-Disposition: form-data; name="file1"; filename="example.txt"
Content-Type: text/plain

Hello, world!
-----------------------------354901075210407969363875912417--'''.replace(b'\n', b'\r\n')

parser = BytesMultiPartParser(headers, input_data)
for headers, content in parser.get_parts():
    print("Headers:", headers)
    print("Content:", content)
```

"""

import re

from duck.exceptions.all import MultiPartParserError


class BytesMultiPartParser:
    """
    A parser for multipart form-data, especially suited for parsing bytes input.

    Attributes:
        headers (dict): The headers of the multipart data.
        input_data (bytes): The raw bytes input data to parse.
        boundary (str): The boundary string extracted from headers.
        parts (list): Parsed parts of the multipart data.
    """

    def __init__(self, headers, input_data):
        """
        Initialize the parser with headers and input data.

        Args:
            headers (dict): The headers of the multipart data.
            input_data (bytes): The raw bytes input data.
        """
        self.headers = headers
        self.input_data = input_data
        self.boundary = self._parse_boundary()
        self.parts = self._parse_parts()

    def _parse_boundary(self):
        """
        Extract the boundary string from the headers.

        Returns:
            str: The boundary string.

        Raises:
            MultiPartParserError: If no boundary isdecode('utf-8')
        """
        content_type = self.headers.get("Content-Type")
        content_type = (content_type.decode("utf-8") if isinstance(
            content_type, bytes) else content_type)

        if not content_type:
            raise MultiPartParserError(
                "Content-Type header is missing from headers")

        match = re.search(r"boundary=(.*)", content_type)

        if not match:
            raise MultiPartParserError(
                "Invalid Content-Type header, no boundary found.")
        return match.group(1).strip()

    def _parse_parts(self):
        """
        Parse the input data into its constituent parts.

        Returns:
            list: A list of tuples, each containing headers and content of a part.

        Raises:
            MultiPartParserError: If an invalid part is encountered during parsing.
        """
        boundary = f"--{self.boundary}".encode("utf-8")
        parts = self.input_data.split(boundary)
        parsed_parts = []
        for part in parts[
                1:-1]:  # Skip the first and last parts (preamble and epilogue)
            if part.strip():
                header_content_split = part.split(b"\r\n\r\n", 1)
                if len(header_content_split) == 2:
                    headers, content = header_content_split
                    parsed_parts.append(
                        (self._parse_headers(headers), content.strip()))
                else:
                    raise MultiPartParserError(
                        "Invalid part encountered during parsing.")
        return parsed_parts

    def _parse_headers(self, raw_headers):
        """
        Parse raw headers into a dictionary.

        Args:
            raw_headers (bytes): The raw headers in bytes.

        Returns:
            dict: Parsed headers as a dictionary.

        Raises:
            MultiPartParserError: If an invalid header line is encountered.
        """
        headers = {}
        for line in raw_headers.decode("utf-8").split("\r\n"):
            if not line:
                continue
            if ":" in line:  # Check if the line contains a colon
                key, value = line.split(":", 1)
                headers[key.strip().title()] = value.strip()
            else:
                raise MultiPartParserError(f"Invalid header line: {line}")
        return headers

    def get_parts(self):
        """
        Get the parsed parts of the multipart data.

        Returns:
            list: A list of tuples, each containing headers and content of a part.
        """
        return self.parts
