"""
Headers utilities module.
"""
from typing import Dict, List


def parse_headers_from_bytes(data: bytes, delimiter: str = "\r\n") -> Dict[str, List[str]]:
    """
    Parse headers from bytes and store all headers as lists, even if they appear once.
    
    Args:
        data (bytes): The raw header data in bytes format.
        delimiter (str | bytes): Delimiter separating headers.
    
    Returns:
        Dict[str, List[str]]: A dictionary with header names as keys (in lowercase) and lists of their respective values.
    """
    assert isinstance(data, bytes), "Only bytes is allowed as data."
    delimiter = (delimiter.decode("utf-8") if isinstance(delimiter, bytes) else delimiter)
    
    data = data.strip().decode("utf-8")
    lines = data.split(delimiter)

    headers: Dict[str, List[str]] = {}

    # Parse each line and add to headers dictionary
    for line in lines:
        if ":" in line:
            header, value = line.split(": ", 1)
            header = header.strip().lower()  # Normalize header to lowercase
            value = value.strip()

            # Ensure the header is always a list (even if it's not duplicated)
            if header in headers:
                headers[header].append(value)
            else:
                headers[header] = [value]

    return headers
