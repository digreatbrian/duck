import fnmatch
from typing import Optional


def process_wildcards(pattern: str, strings: list[str]) -> Optional[list[str]]:
    """
    Filters a list of strings based on a wildcard pattern.

    Args:
        pattern: The wildcard pattern to match against.
        strings: A list of strings to use

    Returns:
        A list of strings that match the pattern.
    """
    return fnmatch.filter(strings, pattern)
