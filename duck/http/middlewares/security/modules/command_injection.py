"""Module for testing if Command Injection is in url"""

import re


def check_command_injection_in_url(url: str) -> bool:
    """
    Checks for potential command injection patterns in a URL.

    Args:
        url: The URL to check.

    Returns:
        True if a command injection pattern is found, False otherwise.
    """

    command_injection_patterns = [
        r"[;|&`$()<>]",  # Common command separators and special characters
        r"\\",  # Backslash (can be used for escaping)
    ]

    for pattern in command_injection_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return True
    return False
