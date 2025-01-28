import re
from urllib.parse import parse_qs, urlparse


def is_safe_url(url: str) -> bool:
    """
    Checks if a URL is safe from SQL injection based on a whitelist approach.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the URL is safe, False otherwise.
    """

    # Whitelist pattern for allowed characters in URL parameters
    whitelist_pattern = re.compile(r"^[^<>&\"\\\\]+$")

    # Parse URL and extract query parameters
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    # Check if all parameters match the whitelist pattern
    for param_values in query_params.values():
        if not all(
                whitelist_pattern.fullmatch(value) for value in param_values):
            return False

    return True


def check_sql_injection_in_url(url: str) -> bool:
    """
    Checks for potential SQL injection in a URL using a combined approach.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if potential SQL injection is detected, False otherwise.
    """

    # Perform whitelist check first
    if is_safe_url(url):
        return False

    # Basic SQL injection patterns (use with caution due to limitations)
    patterns = [
        r"\b(SELECT|UPDATE|INSERT|DELETE|DROP|ALTER|UNION|WHERE|GROUP BY|HAVING|ORDER BY)\b",
        r"[;=\\\-]",  # SQL syntax characters
        r"\b(AND|OR|NOT|LIKE|IN|BETWEEN)\b",  # Logical operators
        r"'\s*\w+\s*'",  # Single quoted strings
        r"\"\s*\w+\s*\"",  # Double quoted strings
        r"\b(admin|password|table_name|column_name)\b",  # Sensitive keywords
    ]

    # Combine patterns into a single regular expression
    combined_pattern = re.compile("|".join(patterns), re.IGNORECASE)

    # Check if any of the patterns match in the URL
    return bool(combined_pattern.search(url))
