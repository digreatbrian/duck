"""
Module for checking URL command injection.
"""

import re

# Pre-compile the patterns for re-use and speed
CMD_INJ_PATTERN = re.compile(r"[;|&`$()<>\\]")


def check_command_injection_in_url(url: str) -> bool:
    """
    Ultra-fast check for potential command injection patterns in a URL.

    Args:
        url: The URL to check.

    Returns:
        True if a command injection pattern is found, False otherwise.
    """
    # Single pre-compiled regex for max speed (covers all patterns)
    return bool(CMD_INJ_PATTERN.search(url))
